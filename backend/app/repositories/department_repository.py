import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.department import Department


def list_for_project(db: Session, project_id: uuid.UUID) -> List[Department]:
    return db.query(Department).filter(Department.project_id == project_id).order_by(Department.name).all()


def get_by_id(db: Session, department_id: uuid.UUID) -> Optional[Department]:
    return db.get(Department, department_id)


def create(db: Session, department: Department) -> Department:
    db.add(department)
    db.flush()
    return department
