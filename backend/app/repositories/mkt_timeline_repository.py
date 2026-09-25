import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.mkt_timeline import MktTimelineItem


def get_by_id(db: Session, item_id: uuid.UUID) -> Optional[MktTimelineItem]:
    return db.get(MktTimelineItem, item_id)


def list_for_project(db: Session, project_id: uuid.UUID) -> List[MktTimelineItem]:
    return (
        db.query(MktTimelineItem)
        .filter(MktTimelineItem.project_id == project_id)
        .order_by(MktTimelineItem.start_date)
        .all()
    )


def create(db: Session, item: MktTimelineItem) -> MktTimelineItem:
    db.add(item)
    db.flush()
    return item
