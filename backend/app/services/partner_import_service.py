import csv
import io
import re
import uuid
from typing import Dict, List, Optional

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.models.enums import ImportBatchStatusEnum, ImportRowStatusEnum, PartnerStatusEnum, PartnerTypeEnum
from app.models.import_batch import ImportBatch, ImportRow
from app.models.partner import Partner
from app.models.user import User
from app.repositories import import_repository, partner_repository
from app.services.activity_log_service import log_activity
from app.utils.normalize import normalize_company_name

REQUIRED_COLUMNS = {"company_name"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ImportServiceError(ValueError):
    pass


def _sanitize_row(row: dict) -> Dict[str, Optional[str]]:
    """Normalizes column names (lowercase, stripped) and stringifies every
    value so raw_data is always plain JSON — xlsx cells can come back as
    datetime/int/float objects, which JSONB can't store directly."""
    sanitized: Dict[str, Optional[str]] = {}
    for key, value in row.items():
        clean_key = (key or "").strip().lower()
        if value is None:
            sanitized[clean_key] = None
        else:
            sanitized[clean_key] = str(value).strip()
    return sanitized


def _parse_csv(file_bytes: bytes) -> List[dict]:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [_sanitize_row(row) for row in reader]


def _parse_xlsx(file_bytes: bytes) -> List[dict]:
    workbook = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    sheet = workbook.active
    rows_iter = sheet.iter_rows(values_only=True)

    try:
        headers = [str(h).strip().lower() if h is not None else "" for h in next(rows_iter)]
    except StopIteration:
        return []

    rows = []
    for raw_row in rows_iter:
        if raw_row is None or all(cell is None for cell in raw_row):
            continue
        row_dict = {headers[i]: raw_row[i] for i in range(min(len(headers), len(raw_row)))}
        rows.append(_sanitize_row(row_dict))
    return rows


def parse_file(filename: str, file_bytes: bytes) -> List[dict]:
    lower = (filename or "").lower()
    if lower.endswith(".csv"):
        return _parse_csv(file_bytes)
    if lower.endswith(".xlsx"):
        return _parse_xlsx(file_bytes)
    raise ImportServiceError("Only .csv and .xlsx files are supported.")


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


def validate_and_stage_rows(db: Session, *, actor: User, filename: str, rows: List[dict]) -> ImportBatch:
    """Parses, validates, and tags every row NEW / DUPLICATE / ERROR without
    creating a single Partner record yet. This is the spec's 'Import Preview'
    step (section 18) — the Admin sees exact counts and per-row problems
    before anything touches the live database."""
    if not rows:
        raise ImportServiceError("The file has no data rows.")

    header_keys = set(rows[0].keys())
    missing = REQUIRED_COLUMNS - header_keys
    if missing:
        raise ImportServiceError(f"Missing required column(s): {', '.join(sorted(missing))}")

    batch = ImportBatch(
        uploaded_by_id=actor.id,
        file_name=filename,
        status=ImportBatchStatusEnum.PENDING,
        total_rows=len(rows),
    )
    import_repository.create_batch(db, batch)
    db.flush()

    seen_in_file: set = set()
    new_count = duplicate_count = error_count = 0

    for row in rows:
        company_name = _clean(row.get("company_name"))
        email = _clean(row.get("email"))
        partner_type_raw = _clean(row.get("partner_type"))

        error_message = None
        if not company_name:
            error_message = "company_name is required."
        elif email and not EMAIL_RE.match(email):
            error_message = f"Invalid email format: {email}"
        elif partner_type_raw and partner_type_raw.upper() not in PartnerTypeEnum.__members__:
            error_message = f"Unknown partner_type: {partner_type_raw}"

        if error_message:
            import_repository.create_row(
                db,
                ImportRow(
                    import_batch_id=batch.id,
                    raw_data=row,
                    row_status=ImportRowStatusEnum.ERROR,
                    error_message=error_message,
                ),
            )
            error_count += 1
            continue

        normalized = normalize_company_name(company_name)
        existing_partner = partner_repository.get_by_normalized_name(db, normalized)

        if existing_partner is not None or normalized in seen_in_file:
            import_repository.create_row(
                db,
                ImportRow(
                    import_batch_id=batch.id,
                    raw_data=row,
                    row_status=ImportRowStatusEnum.DUPLICATE,
                    resolved_partner_id=existing_partner.id if existing_partner else None,
                ),
            )
            duplicate_count += 1
            continue

        seen_in_file.add(normalized)
        import_repository.create_row(
            db, ImportRow(import_batch_id=batch.id, raw_data=row, row_status=ImportRowStatusEnum.NEW)
        )
        new_count += 1

    batch.new_count = new_count
    batch.duplicate_count = duplicate_count
    batch.error_count = error_count
    batch.status = ImportBatchStatusEnum.VALIDATED
    db.commit()
    db.refresh(batch)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_IMPORT_VALIDATED",
        entity_type="ImportBatch",
        entity_id=batch.id,
        description=(
            f"{actor.full_name} uploaded '{filename}': "
            f"{new_count} new, {duplicate_count} duplicate, {error_count} error rows."
        ),
    )
    db.commit()
    return batch


def commit_import(db: Session, *, actor: User, batch_id: uuid.UUID) -> ImportBatch:
    """Inserts only rows tagged NEW as real Partner records. DUPLICATE and
    ERROR rows are never inserted — the spec (section 18) is explicit that
    duplicates must never be silently created, even in bulk."""
    batch = import_repository.get_batch(db, batch_id)
    if batch is None:
        raise ImportServiceError("Import batch not found.")
    if batch.status == ImportBatchStatusEnum.COMMITTED:
        raise ImportServiceError("This import batch has already been committed.")

    created = 0
    for row in batch.rows:
        if row.row_status != ImportRowStatusEnum.NEW:
            continue

        data = row.raw_data
        company_name = _clean(data.get("company_name"))
        normalized = normalize_company_name(company_name)

        # Re-check at commit time in case something else created this partner
        # between validation and commit — never trust a stale preview.
        if partner_repository.get_by_normalized_name(db, normalized):
            row.row_status = ImportRowStatusEnum.DUPLICATE
            continue

        partner_type_raw = _clean(data.get("partner_type"))
        partner_type = (
            PartnerTypeEnum[partner_type_raw.upper()]
            if partner_type_raw and partner_type_raw.upper() in PartnerTypeEnum.__members__
            else PartnerTypeEnum.OTHER
        )

        partner = Partner(
            company_name=company_name,
            normalized_name=normalized,
            industry=_clean(data.get("industry")),
            contact_person=_clean(data.get("contact_person")),
            email=_clean(data.get("email")),
            phone=_clean(data.get("phone")),
            address=_clean(data.get("address")),
            city=_clean(data.get("city")),
            website=_clean(data.get("website")),
            partner_type=partner_type,
            status=PartnerStatusEnum.NEW,
            notes=_clean(data.get("notes")),
            created_by_id=actor.id,
        )
        db.add(partner)
        db.flush()
        row.resolved_partner_id = partner.id
        created += 1

    batch.status = ImportBatchStatusEnum.COMMITTED
    db.commit()
    db.refresh(batch)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_IMPORT_COMMITTED",
        entity_type="ImportBatch",
        entity_id=batch.id,
        description=f"{actor.full_name} committed import '{batch.file_name}': {created} partners created.",
    )
    db.commit()
    return batch
