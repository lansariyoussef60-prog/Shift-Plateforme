import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import import_repository
from app.schemas.import_batch import ImportBatchOut, ImportPreviewOut
from app.services.partner_import_service import (
    ImportServiceError,
    commit_import,
    parse_file,
    validate_and_stage_rows,
)

router = APIRouter(prefix="/partners/import", tags=["partner-import"])


def _to_preview(db: Session, batch_id: uuid.UUID) -> ImportPreviewOut:
    batch = import_repository.get_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found.")
    return ImportPreviewOut.model_validate(batch)


@router.post("", response_model=ImportPreviewOut, status_code=status.HTTP_201_CREATED)
async def upload_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_IMPORT)),
):
    file_bytes = await file.read()
    try:
        rows = parse_file(file.filename or "", file_bytes)
        batch = validate_and_stage_rows(db, actor=current_user, filename=file.filename or "upload", rows=rows)
    except ImportServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _to_preview(db, batch.id)


@router.get("/{batch_id}/preview", response_model=ImportPreviewOut)
def get_preview(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_IMPORT)),
):
    return _to_preview(db, batch_id)


@router.post("/{batch_id}/commit", response_model=ImportBatchOut)
def commit(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_IMPORT)),
):
    try:
        return commit_import(db, actor=current_user, batch_id=batch_id)
    except ImportServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
