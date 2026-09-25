import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import speaker_repository
from app.schemas.speaker import (
    SpeakerContactCreate,
    SpeakerContactOut,
    SpeakerCreate,
    SpeakerHistoryOut,
    SpeakerOut,
    SpeakerSearchResult,
    SpeakerStatusUpdate,
    SpeakerUpdate,
)
from app.services import speaker_service
from app.services.speaker_service import SpeakerServiceError

router = APIRouter(prefix="/speakers", tags=["speakers"])


@router.get("", response_model=List[SpeakerOut])
def list_speakers(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return speaker_repository.list_all(db, limit=limit, offset=offset)


@router.get("/search", response_model=List[SpeakerSearchResult])
def search_speakers(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []
    for speaker in speaker_service.search_speakers(db, q):
        latest_contact = speaker_repository.get_latest_contact(db, speaker.id)
        results.append(
            SpeakerSearchResult(
                speaker=SpeakerOut.model_validate(speaker),
                already_contacted=speaker.status.value != "PROSPECT",
                last_contact=SpeakerContactOut.model_validate(latest_contact) if latest_contact else None,
            )
        )
    return results


@router.post("", response_model=SpeakerOut, status_code=status.HTTP_201_CREATED)
def create_speaker_endpoint(
    payload: SpeakerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.SPEAKER_MANAGE)),
):
    try:
        return speaker_service.create_speaker(
            db,
            actor=current_user,
            name=payload.name,
            organization=payload.organization,
            position=payload.position,
            email=payload.email,
            phone=payload.phone,
            linkedin=payload.linkedin,
            topic=payload.topic,
            notes=payload.notes,
        )
    except SpeakerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{speaker_id}", response_model=SpeakerOut)
def get_speaker(
    speaker_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    speaker = speaker_repository.get_by_id(db, speaker_id)
    if speaker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker not found.")
    return speaker


@router.get("/{speaker_id}/history", response_model=SpeakerHistoryOut)
def get_speaker_history(
    speaker_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    speaker = speaker_repository.get_by_id(db, speaker_id)
    if speaker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker not found.")
    return SpeakerHistoryOut(
        speaker=SpeakerOut.model_validate(speaker),
        contacts=[SpeakerContactOut.model_validate(c) for c in speaker_repository.list_contacts(db, speaker_id)],
    )


@router.put("/{speaker_id}", response_model=SpeakerOut)
def update_speaker_endpoint(
    speaker_id: uuid.UUID,
    payload: SpeakerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.SPEAKER_MANAGE)),
):
    try:
        return speaker_service.update_speaker(
            db, actor=current_user, speaker_id=speaker_id, updates=payload.model_dump(exclude_unset=True)
        )
    except SpeakerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{speaker_id}/status", response_model=SpeakerOut)
def change_speaker_status(
    speaker_id: uuid.UUID,
    payload: SpeakerStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.SPEAKER_MANAGE)),
):
    try:
        return speaker_service.change_status(
            db, actor=current_user, speaker_id=speaker_id, new_status=payload.status
        )
    except SpeakerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{speaker_id}/contacts", response_model=SpeakerContactOut, status_code=status.HTTP_201_CREATED
)
def add_speaker_contact(
    speaker_id: uuid.UUID,
    payload: SpeakerContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.SPEAKER_CONTACT_LOG)),
):
    try:
        return speaker_service.add_contact(
            db,
            actor=current_user,
            speaker_id=speaker_id,
            contact_method=payload.contact_method,
            result=payload.result,
            notes=payload.notes,
        )
    except SpeakerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
