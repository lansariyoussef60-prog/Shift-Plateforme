import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User


def log_activity(
    db: Session,
    *,
    actor: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
) -> ActivityLog:
    """Every sensitive service-layer action calls this. Routers never write to
    ActivityLog directly — that would let a new endpoint silently skip auditing."""
    entry = ActivityLog(
        actor_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    db.add(entry)
    db.flush()
    return entry
