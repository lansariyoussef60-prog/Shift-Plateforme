import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import TargetListItemStatusEnum
from app.models.target_list import TargetList
from app.models.target_list_item import TargetListItem
from app.models.user import User
from app.repositories import target_list_repository
from app.services.activity_log_service import log_activity
from app.services.partner_service import find_exact_match, get_or_create_partner_for_target_list


class TargetListServiceError(ValueError):
    pass


def create_target_list(
    db: Session, *, actor: User, name: str, department_id: Optional[uuid.UUID], project_id: uuid.UUID
) -> TargetList:
    target_list = TargetList(
        name=name.strip(), owner_id=actor.id, department_id=department_id, project_id=project_id
    )
    target_list_repository.create(db, target_list)
    db.commit()
    db.refresh(target_list)
    return target_list


def add_item(
    db: Session,
    *,
    actor: User,
    target_list_id: uuid.UUID,
    company_name: str,
    allow_override: bool,
) -> TargetListItem:
    """The workflow from spec section 16: resolve company_name to a Partner
    (existing or newly created), enforce the already-contacted block
    server-side (this call may raise DuplicatePartnerBlockedError, which the
    router turns into a 409 with full history — see partner_service for why
    the block itself lives there, not here), and only then create the list
    item, respecting the UNIQUE(target_list_id, partner_id) constraint."""
    target_list = target_list_repository.get_by_id(db, target_list_id)
    if target_list is None:
        raise TargetListServiceError("Target list not found.")

    # Check "already on THIS list" before the global already-contacted block:
    # if the partner is already an item here, that's a more specific and more
    # useful error than re-litigating whether it was ever contacted.
    existing_partner = find_exact_match(db, company_name)
    if existing_partner is not None:
        existing_item = target_list_repository.get_item_by_partner(db, target_list_id, existing_partner.id)
        if existing_item is not None:
            raise TargetListServiceError(f"{existing_partner.company_name} is already on this list.")

    partner = get_or_create_partner_for_target_list(
        db, actor=actor, company_name=company_name, allow_override=allow_override
    )

    if target_list_repository.get_item_by_partner(db, target_list_id, partner.id) is not None:
        raise TargetListServiceError(f"{partner.company_name} is already on this list.")

    item = TargetListItem(
        target_list_id=target_list_id,
        partner_id=partner.id,
        status=TargetListItemStatusEnum.PROSPECT,
        added_by_id=actor.id,
    )
    db.add(item)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise TargetListServiceError(f"{partner.company_name} is already on this list.") from exc

    db.refresh(item)

    log_activity(
        db,
        actor=actor,
        action="TARGET_LIST_ITEM_ADDED",
        entity_type="TargetList",
        entity_id=target_list.id,
        description=f"{actor.full_name} added {partner.company_name} to target list '{target_list.name}'.",
    )
    db.commit()
    return item


def update_item_status(
    db: Session, *, actor: User, item_id: uuid.UUID, new_status: TargetListItemStatusEnum
) -> TargetListItem:
    item = target_list_repository.get_item(db, item_id)
    if item is None:
        raise TargetListServiceError("Target list item not found.")

    old_status = item.status
    item.status = new_status
    db.commit()
    db.refresh(item)

    log_activity(
        db,
        actor=actor,
        action="TARGET_LIST_ITEM_STATUS_CHANGED",
        entity_type="TargetListItem",
        entity_id=item.id,
        description=f"{actor.full_name} changed item status from {old_status.value} to {new_status.value}.",
    )
    db.commit()
    return item
