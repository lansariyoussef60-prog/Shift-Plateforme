import uuid
from datetime import date as date_cls
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import ContactMethodEnum, PartnerStatusEnum, PartnerTypeEnum
from app.models.partner import Partner
from app.models.partner_collaboration import PartnerCollaboration
from app.models.partner_contact import PartnerContact
from app.models.user import User
from app.repositories import partner_repository
from app.services.activity_log_service import log_activity
from app.utils.normalize import normalize_company_name


class PartnerServiceError(ValueError):
    """Raised for any business-rule violation; routers translate this to an
    appropriate HTTP status (400 for bad input, 404 for missing records)."""


class DuplicatePartnerBlockedError(ValueError):
    """Raised when a caller tries to add an already-contacted partner as a
    fresh prospect without authorization to override. Carries the partner and
    its latest contact so the caller (the target-list router) can return a
    rich 409 body with full history — this is the server-side enforcement of
    the 'already contacted' rule described in the spec; it never depends on
    the frontend having checked first."""

    def __init__(self, partner: Partner, latest_contact: Optional[PartnerContact]):
        self.partner = partner
        self.latest_contact = latest_contact
        super().__init__(f"{partner.company_name} has already been contacted.")


def search_partners(db: Session, query: str) -> List[Partner]:
    normalized_query = normalize_company_name(query)
    if not normalized_query:
        return []
    return partner_repository.search(db, normalized_query)


def find_exact_match(db: Session, company_name: str) -> Optional[Partner]:
    return partner_repository.get_by_normalized_name(db, normalize_company_name(company_name))


def create_partner(
    db: Session,
    *,
    actor: User,
    company_name: str,
    industry: Optional[str] = None,
    contact_person: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    website: Optional[str] = None,
    partner_type: PartnerTypeEnum = PartnerTypeEnum.OTHER,
    notes: Optional[str] = None,
) -> Partner:
    normalized = normalize_company_name(company_name)
    if not normalized:
        raise PartnerServiceError("Company name cannot be empty.")

    if partner_repository.get_by_normalized_name(db, normalized):
        raise PartnerServiceError(f"A partner named '{company_name}' already exists.")

    partner = Partner(
        company_name=company_name.strip(),
        normalized_name=normalized,
        industry=industry,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address,
        city=city,
        website=website,
        partner_type=partner_type,
        status=PartnerStatusEnum.NEW,
        notes=notes,
        created_by_id=actor.id,
    )

    try:
        partner_repository.create(db, partner)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PartnerServiceError(f"A partner named '{company_name}' already exists.") from exc

    db.refresh(partner)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_CREATED",
        entity_type="Partner",
        entity_id=partner.id,
        description=f"{actor.full_name} added partner {partner.company_name}.",
    )
    db.commit()
    return partner


def get_or_create_partner_for_target_list(
    db: Session, *, actor: User, company_name: str, allow_override: bool
) -> Partner:
    """The core dedup rule described in the spec's section 14/16: search the
    centralized Partner table by normalized name. No match -> silently create
    a fresh NEW partner. A match that has moved past NEW (i.e. it has been
    contacted at least once) is blocked from being re-added as a fresh
    prospect, unless the caller is authorized to override — checked by the
    caller via allow_override, itself derived from the actor's role, never
    from anything the request body claims about permissions."""
    existing = find_exact_match(db, company_name)

    if existing is None:
        return create_partner(db, actor=actor, company_name=company_name)

    if existing.status != PartnerStatusEnum.NEW and not allow_override:
        latest_contact = partner_repository.get_latest_contact(db, existing.id)
        raise DuplicatePartnerBlockedError(existing, latest_contact)

    return existing


def add_contact(
    db: Session,
    *,
    actor: User,
    partner_id: uuid.UUID,
    contact_method: ContactMethodEnum,
    result: Optional[str],
    notes: Optional[str],
    follow_up_date: Optional[date_cls],
    project_id: Optional[uuid.UUID],
) -> PartnerContact:
    partner = partner_repository.get_by_id(db, partner_id)
    if partner is None:
        raise PartnerServiceError("Partner not found.")

    contact = PartnerContact(
        partner_id=partner.id,
        user_id=actor.id,
        project_id=project_id,
        contact_method=contact_method,
        result=result,
        notes=notes,
        follow_up_date=follow_up_date,
    )
    db.add(contact)

    # Advance the partner's global status the first time it's contacted.
    # Later contacts don't force a status change — a manager may have already
    # moved it to NEGOTIATION, and a routine follow-up shouldn't roll that back.
    if partner.status == PartnerStatusEnum.NEW:
        partner.status = PartnerStatusEnum.CONTACTED

    partner.last_contact_date = date_cls.today()
    partner.last_contacted_by_id = actor.id

    db.commit()
    db.refresh(contact)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_CONTACT_LOGGED",
        entity_type="Partner",
        entity_id=partner.id,
        description=f"{actor.full_name} logged a contact with {partner.company_name}.",
    )
    db.commit()
    return contact


def update_official_fields(db: Session, *, actor: User, partner_id: uuid.UUID, updates: dict) -> Partner:
    """Only reachable via Action.PARTNER_EDIT_OFFICIAL — ordinary OC members
    never get a route to this function at all."""
    partner = partner_repository.get_by_id(db, partner_id)
    if partner is None:
        raise PartnerServiceError("Partner not found.")

    for field, value in updates.items():
        if value is None:
            continue
        if field == "company_name":
            partner.company_name = value
            partner.normalized_name = normalize_company_name(value)
        else:
            setattr(partner, field, value)

    db.commit()
    db.refresh(partner)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_UPDATED",
        entity_type="Partner",
        entity_id=partner.id,
        description=f"{actor.full_name} updated partner {partner.company_name}.",
    )
    db.commit()
    return partner


def change_status(db: Session, *, actor: User, partner_id: uuid.UUID, new_status: PartnerStatusEnum) -> Partner:
    partner = partner_repository.get_by_id(db, partner_id)
    if partner is None:
        raise PartnerServiceError("Partner not found.")

    old_status = partner.status
    partner.status = new_status
    db.commit()
    db.refresh(partner)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_STATUS_CHANGED",
        entity_type="Partner",
        entity_id=partner.id,
        description=(
            f"{actor.full_name} changed {partner.company_name}'s status "
            f"from {old_status.value} to {new_status.value}."
        ),
    )
    db.commit()
    return partner


def add_collaboration(
    db: Session,
    *,
    actor: User,
    partner_id: uuid.UUID,
    project_id: uuid.UUID,
    title: str,
    amount_value: Optional[Decimal],
    currency: Optional[str],
    notes: Optional[str],
) -> PartnerCollaboration:
    partner = partner_repository.get_by_id(db, partner_id)
    if partner is None:
        raise PartnerServiceError("Partner not found.")

    collaboration = PartnerCollaboration(
        partner_id=partner.id,
        project_id=project_id,
        title=title,
        amount_value=amount_value,
        currency=currency or "TND",
        confirmed_by_id=actor.id,
        notes=notes,
    )
    db.add(collaboration)
    db.commit()
    db.refresh(collaboration)

    log_activity(
        db,
        actor=actor,
        action="PARTNER_COLLABORATION_ADDED",
        entity_type="Partner",
        entity_id=partner.id,
        description=f"{actor.full_name} recorded a collaboration '{title}' with {partner.company_name}.",
    )
    db.commit()
    return collaboration
