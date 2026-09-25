import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import MktStatusEnum, TaskPriorityEnum
from app.models.mkt_timeline import MktTimelineItem
from app.models.user import User
from app.repositories import mkt_timeline_repository
from app.services.activity_log_service import log_activity


class MktTimelineServiceError(ValueError):
    pass


def create_item(
    db: Session,
    *,
    actor: User,
    title: str,
    description: Optional[str],
    start_date: date,
    end_date: Optional[date],
    responsible_id: Optional[uuid.UUID],
    department_id: Optional[uuid.UUID],
    project_id: uuid.UUID,
    priority: TaskPriorityEnum,
    related_task_id: Optional[uuid.UUID],
    notes: Optional[str],
) -> MktTimelineItem:
    if end_date is not None and end_date < start_date:
        raise MktTimelineServiceError("end_date cannot be before start_date.")

    item = MktTimelineItem(
        title=title.strip(),
        description=description,
        start_date=start_date,
        end_date=end_date,
        responsible_id=responsible_id,
        department_id=department_id,
        project_id=project_id,
        status=MktStatusEnum.PLANNED,
        priority=priority,
        related_task_id=related_task_id,
        notes=notes,
    )
    mkt_timeline_repository.create(db, item)
    db.commit()
    db.refresh(item)

    log_activity(
        db,
        actor=actor,
        action="MKT_TIMELINE_ITEM_CREATED",
        entity_type="MktTimelineItem",
        entity_id=item.id,
        description=f"{actor.full_name} added timeline item '{item.title}'.",
    )
    db.commit()
    return item


def update_status(db: Session, *, actor: User, item_id: uuid.UUID, new_status: MktStatusEnum) -> MktTimelineItem:
    item = mkt_timeline_repository.get_by_id(db, item_id)
    if item is None:
        raise MktTimelineServiceError("Timeline item not found.")

    old_status = item.status
    item.status = new_status
    db.commit()
    db.refresh(item)

    log_activity(
        db,
        actor=actor,
        action="MKT_TIMELINE_ITEM_STATUS_CHANGED",
        entity_type="MktTimelineItem",
        entity_id=item.id,
        description=f"{actor.full_name} changed '{item.title}' status from {old_status.value} to {new_status.value}.",
    )
    db.commit()
    return item
