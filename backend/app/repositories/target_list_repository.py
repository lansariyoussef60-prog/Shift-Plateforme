import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.target_list import TargetList
from app.models.target_list_item import TargetListItem


def get_by_id(db: Session, target_list_id: uuid.UUID) -> Optional[TargetList]:
    return db.get(TargetList, target_list_id)


def list_for_user(db: Session, owner_id: Optional[uuid.UUID] = None) -> List[TargetList]:
    query = db.query(TargetList)
    if owner_id is not None:
        query = query.filter(TargetList.owner_id == owner_id)
    return query.order_by(TargetList.created_at.desc()).all()


def create(db: Session, target_list: TargetList) -> TargetList:
    db.add(target_list)
    db.flush()
    return target_list


def get_item(db: Session, item_id: uuid.UUID) -> Optional[TargetListItem]:
    return db.get(TargetListItem, item_id)


def list_items(db: Session, target_list_id: uuid.UUID) -> List[TargetListItem]:
    return (
        db.query(TargetListItem)
        .options(joinedload(TargetListItem.partner))
        .filter(TargetListItem.target_list_id == target_list_id)
        .order_by(TargetListItem.added_at.desc())
        .all()
    )


def get_item_by_partner(
    db: Session, target_list_id: uuid.UUID, partner_id: uuid.UUID
) -> Optional[TargetListItem]:
    return (
        db.query(TargetListItem)
        .filter(TargetListItem.target_list_id == target_list_id, TargetListItem.partner_id == partner_id)
        .first()
    )
