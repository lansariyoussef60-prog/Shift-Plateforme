import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.invite import Invite


def get_by_token(db: Session, token: str) -> Optional[Invite]:
    return db.query(Invite).filter(Invite.token == token).first()


def get_by_id(db: Session, invite_id: uuid.UUID) -> Optional[Invite]:
    return db.get(Invite, invite_id)


def list_all(db: Session, limit: int = 100) -> List[Invite]:
    return db.query(Invite).order_by(Invite.created_at.desc()).limit(limit).all()


def create(db: Session, invite: Invite) -> Invite:
    db.add(invite)
    db.flush()
    return invite


def revoke(db: Session, invite: Invite) -> Invite:
    invite.used_at = datetime.now(timezone.utc)
    db.flush()
    return invite


def revoke_pending_for_email(db: Session, email: str) -> None:
    """Soft-revokes any not-yet-used invite for this email by marking it used
    — so issuing a new invite always invalidates any old, unclicked link for
    the same address."""
    db.query(Invite).filter(Invite.email == email, Invite.used_at.is_(None)).update(
        {"used_at": datetime.now(timezone.utc)}, synchronize_session=False
    )