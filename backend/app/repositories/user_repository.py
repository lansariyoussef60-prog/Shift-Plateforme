import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def list_users(db: Session, department_id: Optional[uuid.UUID] = None) -> List[User]:
    query = db.query(User)
    if department_id is not None:
        query = query.filter(User.department_id == department_id)
    return query.order_by(User.full_name).all()


def list_direct_reports(db: Session, manager_id: uuid.UUID) -> List[User]:
    return db.query(User).filter(User.manager_id == manager_id).order_by(User.full_name).all()


def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user
