import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project


def list_all(db: Session) -> List[Project]:
    return db.query(Project).order_by(Project.name).all()


def get_by_id(db: Session, project_id: uuid.UUID) -> Optional[Project]:
    return db.get(Project, project_id)


def create(db: Session, project: Project) -> Project:
    db.add(project)
    db.flush()
    return project
