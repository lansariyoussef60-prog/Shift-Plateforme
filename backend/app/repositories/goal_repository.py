import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.goal import Goal


def get_by_id(db: Session, goal_id: uuid.UUID) -> Optional[Goal]:
    return db.get(Goal, goal_id)


def list_for_project(db: Session, project_id: uuid.UUID) -> List[Goal]:
    return db.query(Goal).filter(Goal.project_id == project_id).order_by(Goal.created_at.desc()).all()


def create(db: Session, goal: Goal) -> Goal:
    db.add(goal)
    db.flush()
    return goal
