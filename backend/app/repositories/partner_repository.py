import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.partner import Partner
from app.models.partner_collaboration import PartnerCollaboration
from app.models.partner_contact import PartnerContact


def get_by_id(db: Session, partner_id: uuid.UUID) -> Optional[Partner]:
    return db.get(Partner, partner_id)


def get_by_normalized_name(db: Session, normalized_name: str) -> Optional[Partner]:
    return db.query(Partner).filter(Partner.normalized_name == normalized_name).first()


def search(db: Session, normalized_query: str, limit: int = 20) -> List[Partner]:
    like_pattern = f"%{normalized_query}%"
    return (
        db.query(Partner)
        .filter(Partner.normalized_name.ilike(like_pattern))
        .order_by(Partner.company_name)
        .limit(limit)
        .all()
    )


def list_all(db: Session, limit: int = 100, offset: int = 0) -> List[Partner]:
    return db.query(Partner).order_by(Partner.company_name).offset(offset).limit(limit).all()


def create(db: Session, partner: Partner) -> Partner:
    db.add(partner)
    db.flush()
    return partner


def list_contacts(db: Session, partner_id: uuid.UUID) -> List[PartnerContact]:
    return (
        db.query(PartnerContact)
        .filter(PartnerContact.partner_id == partner_id)
        .order_by(PartnerContact.created_at.desc())
        .all()
    )


def list_collaborations(db: Session, partner_id: uuid.UUID) -> List[PartnerCollaboration]:
    return (
        db.query(PartnerCollaboration)
        .filter(PartnerCollaboration.partner_id == partner_id)
        .order_by(PartnerCollaboration.confirmed_at.desc())
        .all()
    )


def get_latest_contact(db: Session, partner_id: uuid.UUID) -> Optional[PartnerContact]:
    return (
        db.query(PartnerContact)
        .filter(PartnerContact.partner_id == partner_id)
        .order_by(PartnerContact.created_at.desc())
        .first()
    )
