import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.speaker import Speaker
from app.models.speaker_contact import SpeakerContact


def get_by_id(db: Session, speaker_id: uuid.UUID) -> Optional[Speaker]:
    return db.get(Speaker, speaker_id)


def get_by_normalized_name(db: Session, normalized_name: str) -> Optional[Speaker]:
    return db.query(Speaker).filter(Speaker.normalized_name == normalized_name).first()


def search(db: Session, normalized_query: str, limit: int = 20) -> List[Speaker]:
    like_pattern = f"%{normalized_query}%"
    return (
        db.query(Speaker)
        .filter(Speaker.normalized_name.ilike(like_pattern))
        .order_by(Speaker.name)
        .limit(limit)
        .all()
    )


def list_all(db: Session, limit: int = 100, offset: int = 0) -> List[Speaker]:
    return db.query(Speaker).order_by(Speaker.name).offset(offset).limit(limit).all()


def create(db: Session, speaker: Speaker) -> Speaker:
    db.add(speaker)
    db.flush()
    return speaker


def list_contacts(db: Session, speaker_id: uuid.UUID) -> List[SpeakerContact]:
    return (
        db.query(SpeakerContact)
        .filter(SpeakerContact.speaker_id == speaker_id)
        .order_by(SpeakerContact.created_at.desc())
        .all()
    )


def get_latest_contact(db: Session, speaker_id: uuid.UUID) -> Optional[SpeakerContact]:
    return (
        db.query(SpeakerContact)
        .filter(SpeakerContact.speaker_id == speaker_id)
        .order_by(SpeakerContact.created_at.desc())
        .first()
    )
