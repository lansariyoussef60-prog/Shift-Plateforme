import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ContactMethodEnum, SpeakerStatusEnum


class SpeakerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    organization: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    topic: Optional[str] = None
    notes: Optional[str] = None


class SpeakerUpdate(BaseModel):
    organization: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    topic: Optional[str] = None
    confirmation_status: Optional[str] = None
    notes: Optional[str] = None


class SpeakerStatusUpdate(BaseModel):
    status: SpeakerStatusEnum


class SpeakerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    normalized_name: str
    organization: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    topic: Optional[str] = None
    status: SpeakerStatusEnum
    contacted_by_id: Optional[uuid.UUID] = None
    contact_date: Optional[date] = None
    confirmation_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SpeakerContactCreate(BaseModel):
    contact_method: ContactMethodEnum
    result: Optional[str] = None
    notes: Optional[str] = None


class SpeakerContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    speaker_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    contact_method: ContactMethodEnum
    result: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class SpeakerSearchResult(BaseModel):
    speaker: SpeakerOut
    already_contacted: bool
    last_contact: Optional[SpeakerContactOut] = None


class SpeakerHistoryOut(BaseModel):
    speaker: SpeakerOut
    contacts: List[SpeakerContactOut]
