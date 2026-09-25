import uuid
from datetime import date as date_cls
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import ContactMethodEnum, SpeakerStatusEnum
from app.models.speaker import Speaker
from app.models.speaker_contact import SpeakerContact
from app.models.user import User
from app.repositories import speaker_repository
from app.services.activity_log_service import log_activity
from app.utils.normalize import normalize_company_name


class SpeakerServiceError(ValueError):
    pass


def search_speakers(db: Session, query: str) -> List[Speaker]:
    normalized_query = normalize_company_name(query)
    if not normalized_query:
        return []
    return speaker_repository.search(db, normalized_query)


def create_speaker(
    db: Session,
    *,
    actor: User,
    name: str,
    organization: Optional[str] = None,
    position: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    linkedin: Optional[str] = None,
    topic: Optional[str] = None,
    notes: Optional[str] = None,
) -> Speaker:
    normalized = normalize_company_name(name)
    if not normalized:
        raise SpeakerServiceError("Speaker name cannot be empty.")

    if speaker_repository.get_by_normalized_name(db, normalized):
        raise SpeakerServiceError(f"A speaker named '{name}' already exists.")

    speaker = Speaker(
        name=name.strip(),
        normalized_name=normalized,
        organization=organization,
        position=position,
        email=email,
        phone=phone,
        linkedin=linkedin,
        topic=topic,
        status=SpeakerStatusEnum.PROSPECT,
        notes=notes,
    )

    try:
        speaker_repository.create(db, speaker)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SpeakerServiceError(f"A speaker named '{name}' already exists.") from exc

    db.refresh(speaker)
    log_activity(
        db,
        actor=actor,
        action="SPEAKER_CREATED",
        entity_type="Speaker",
        entity_id=speaker.id,
        description=f"{actor.full_name} added speaker {speaker.name}.",
    )
    db.commit()
    return speaker


def update_speaker(db: Session, *, actor: User, speaker_id: uuid.UUID, updates: dict) -> Speaker:
    speaker = speaker_repository.get_by_id(db, speaker_id)
    if speaker is None:
        raise SpeakerServiceError("Speaker not found.")

    for field, value in updates.items():
        if value is not None:
            setattr(speaker, field, value)

    db.commit()
    db.refresh(speaker)
    log_activity(
        db,
        actor=actor,
        action="SPEAKER_UPDATED",
        entity_type="Speaker",
        entity_id=speaker.id,
        description=f"{actor.full_name} updated speaker {speaker.name}.",
    )
    db.commit()
    return speaker


def change_status(db: Session, *, actor: User, speaker_id: uuid.UUID, new_status: SpeakerStatusEnum) -> Speaker:
    speaker = speaker_repository.get_by_id(db, speaker_id)
    if speaker is None:
        raise SpeakerServiceError("Speaker not found.")

    old_status = speaker.status
    speaker.status = new_status
    db.commit()
    db.refresh(speaker)
    log_activity(
        db,
        actor=actor,
        action="SPEAKER_STATUS_CHANGED",
        entity_type="Speaker",
        entity_id=speaker.id,
        description=f"{actor.full_name} changed {speaker.name}'s status from {old_status.value} to {new_status.value}.",
    )
    db.commit()
    return speaker


def add_contact(
    db: Session,
    *,
    actor: User,
    speaker_id: uuid.UUID,
    contact_method: ContactMethodEnum,
    result: Optional[str],
    notes: Optional[str],
) -> SpeakerContact:
    speaker = speaker_repository.get_by_id(db, speaker_id)
    if speaker is None:
        raise SpeakerServiceError("Speaker not found.")

    contact = SpeakerContact(
        speaker_id=speaker.id, user_id=actor.id, contact_method=contact_method, result=result, notes=notes
    )
    db.add(contact)

    if speaker.status == SpeakerStatusEnum.PROSPECT:
        speaker.status = SpeakerStatusEnum.CONTACTED

    speaker.contacted_by_id = actor.id
    speaker.contact_date = date_cls.today()

    db.commit()
    db.refresh(contact)
    log_activity(
        db,
        actor=actor,
        action="SPEAKER_CONTACT_LOGGED",
        entity_type="Speaker",
        entity_id=speaker.id,
        description=f"{actor.full_name} logged a contact with speaker {speaker.name}.",
    )
    db.commit()
    return contact
