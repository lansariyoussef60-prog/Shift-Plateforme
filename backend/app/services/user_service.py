import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories import user_repository
from app.services.activity_log_service import log_activity
from app.services.hierarchy_service import HierarchyError, validate_manager_assignment


class UserServiceError(ValueError):
    """Raised for any business-rule violation; routers translate this to a 400."""


def create_user(
    db: Session,
    *,
    actor: User,
    full_name: str,
    email: str,
    password: str,
    role: RoleEnum,
    department_id: Optional[uuid.UUID],
    manager_id: Optional[uuid.UUID],
) -> User:
    normalized_email = email.strip().lower()

    if user_repository.get_by_email(db, normalized_email):
        raise UserServiceError(f"A user with email {normalized_email} already exists.")

    manager = user_repository.get_by_id(db, manager_id) if manager_id else None
    if manager_id and manager is None:
        raise UserServiceError("The specified manager does not exist.")

    try:
        validate_manager_assignment(role, manager)
    except HierarchyError as exc:
        raise UserServiceError(str(exc)) from exc

    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        role=role,
        department_id=department_id,
        manager_id=manager.id if manager else None,
        is_active=True,
    )

    try:
        user_repository.create(db, user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UserServiceError(f"A user with email {normalized_email} already exists.") from exc

    db.refresh(user)

    log_activity(
        db,
        actor=actor,
        action="USER_CREATED",
        entity_type="User",
        entity_id=user.id,
        description=f"{actor.full_name} created user {user.email} ({user.role.value}).",
    )
    db.commit()
    return user


def assign_manager(
    db: Session, *, actor: User, user_id: uuid.UUID, manager_id: Optional[uuid.UUID]
) -> User:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise UserServiceError("User not found.")

    manager = user_repository.get_by_id(db, manager_id) if manager_id else None
    if manager_id and manager is None:
        raise UserServiceError("The specified manager does not exist.")

    try:
        validate_manager_assignment(user.role, manager)
    except HierarchyError as exc:
        raise UserServiceError(str(exc)) from exc

    old_manager_email = user.manager.email if user.manager else "none"
    user.manager_id = manager.id if manager else None
    db.commit()
    db.refresh(user)

    log_activity(
        db,
        actor=actor,
        action="USER_MANAGER_ASSIGNED",
        entity_type="User",
        entity_id=user.id,
        description=(
            f"{actor.full_name} changed {user.email}'s manager from {old_manager_email} "
            f"to {manager.email if manager else 'none'}."
        ),
    )
    db.commit()
    return user


def deactivate_user(db: Session, *, actor: User, user_id: uuid.UUID) -> User:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise UserServiceError("User not found.")

    user.is_active = False
    db.commit()
    db.refresh(user)

    log_activity(
        db,
        actor=actor,
        action="USER_DEACTIVATED",
        entity_type="User",
        entity_id=user.id,
        description=f"{actor.full_name} deactivated {user.email}.",
    )
    db.commit()
    return user
