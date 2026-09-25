import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task


def get_by_id(db: Session, task_id: uuid.UUID) -> Optional[Task]:
    return db.get(Task, task_id)


def list_assigned_to(db: Session, user_id: uuid.UUID) -> List[Task]:
    return db.query(Task).filter(Task.assigned_to_id == user_id).order_by(Task.created_at.desc()).all()


def list_created_by(db: Session, user_id: uuid.UUID) -> List[Task]:
    return db.query(Task).filter(Task.created_by_id == user_id).order_by(Task.created_at.desc()).all()


def list_for_team(db: Session, assignee_ids: List[uuid.UUID]) -> List[Task]:
    if not assignee_ids:
        return []
    return (
        db.query(Task)
        .filter(Task.assigned_to_id.in_(assignee_ids))
        .order_by(Task.created_at.desc())
        .all()
    )


def create(db: Session, task: Task) -> Task:
    db.add(task)
    db.flush()
    return task
