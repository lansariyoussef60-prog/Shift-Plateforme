import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.invite import Invite
from app.models.user import User
from app.repositories import invite_repository, user_repository
from app.services.activity_log_service import log_activity
from app.services.hierarchy_service import HierarchyError, validate_manager_assignment


class InviteServiceError(ValueError):
    pass


def create_invite(
    db: Session,
    *,
    actor: User,
    email: str,
    role: RoleEnum,
    department_id: Optional[uuid.UUID],
    manager_id: Optional[uuid.UUID],
) -> Invite:
    normalized_email = email.strip().lower()

    if user_repository.get_by_email(db, normalized_email):
        raise InviteServiceError(f"A user with email {normalized_email} already exists.")

    manager = user_repository.get_by_id(db, manager_id) if manager_id else None
    if manager_id and manager is None:
        raise InviteServiceError("The specified manager does not exist.")

    # Same hierarchy validation as direct user creation, run up front so a
    # bad invite is never sent out in the first place.
    try:
        validate_manager_assignment(role, manager)
    except HierarchyError as exc:
        raise InviteServiceError(str(exc)) from exc

    invite_repository.revoke_pending_for_email(db, normalized_email)

    invite = Invite(
        email=normalized_email,
        role=role,
        department_id=department_id,
        manager_id=manager_id,
        token=secrets.token_urlsafe(32),
        created_by_id=actor.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.INVITE_EXPIRE_DAYS),
    )
    invite_repository.create(db, invite)
    db.commit()
    db.refresh(invite)

    log_activity(
        db, actor=actor, action="INVITE_CREATED", entity_type="Invite", entity_id=invite.id,
        description=f"{actor.full_name} invited {normalized_email} as {role.value}.",
    )
    db.commit()
    return invite


def register_with_invite(db: Session, *, token: str, full_name: str, password: str) -> User:
    invite = invite_repository.get_by_token(db, token)
    if invite is None:
        raise InviteServiceError("Invalid invite link.")
    if invite.used_at is not None:
        raise InviteServiceError("This invite has already been used or was revoked.")
    if invite.expires_at < datetime.now(timezone.utc):
        raise InviteServiceError("This invite has expired. Ask an Admin to send a new one.")
    if user_repository.get_by_email(db, invite.email):
        raise InviteServiceError("An account with this email already exists.")

    manager = user_repository.get_by_id(db, invite.manager_id) if invite.manager_id else None
    # Re-validate at registration time too: the org structure may have
    # changed in the days between the invite being sent and clicked.
    try:
        validate_manager_assignment(invite.role, manager)
    except HierarchyError as exc:
        raise InviteServiceError(str(exc)) from exc

    user = User(
        full_name=full_name.strip(),
        email=invite.email,
        password_hash=hash_password(password),
        role=invite.role,
        department_id=invite.department_id,
        manager_id=invite.manager_id,
        is_active=True,
    )
    db.add(user)
    invite.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    log_activity(
        db, actor=user, action="USER_REGISTERED_VIA_INVITE", entity_type="User", entity_id=user.id,
        description=f"{user.full_name} completed registration via invite.",
    )
    db.commit()
    return user


def revoke_invite(db: Session, *, actor: User, invite_id: uuid.UUID) -> Invite:
    invite = invite_repository.get_by_id(db, invite_id)
    if invite is None:
        raise InviteServiceError("Invite not found.")
    if invite.used_at is not None:
        raise InviteServiceError("This invite has already been used or revoked — nothing to do.")

    invite_repository.revoke(db, invite)
    db.commit()
    db.refresh(invite)

    log_activity(
        db, actor=actor, action="INVITE_REVOKED", entity_type="Invite", entity_id=invite.id,
        description=f"{actor.full_name} revoked the invite sent to {invite.email}.",
    )
    db.commit()
    return invite