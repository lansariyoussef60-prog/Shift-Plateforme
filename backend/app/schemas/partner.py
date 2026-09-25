import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ContactMethodEnum, PartnerStatusEnum, PartnerTypeEnum


class PartnerCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    partner_type: PartnerTypeEnum = PartnerTypeEnum.OTHER
    notes: Optional[str] = None


class PartnerUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    partner_type: Optional[PartnerTypeEnum] = None
    notes: Optional[str] = None


class PartnerStatusUpdate(BaseModel):
    status: PartnerStatusEnum


class PartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    normalized_name: str
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    partner_type: PartnerTypeEnum
    status: PartnerStatusEnum
    last_contact_date: Optional[date] = None
    last_contacted_by_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PartnerContactCreate(BaseModel):
    contact_method: ContactMethodEnum
    result: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    project_id: Optional[uuid.UUID] = None


class PartnerContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    partner_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    contact_method: ContactMethodEnum
    result: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime


class PartnerCollaborationCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=2, max_length=255)
    amount_value: Optional[Decimal] = None
    currency: Optional[str] = "TND"
    notes: Optional[str] = None


class PartnerCollaborationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    partner_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    amount_value: Optional[Decimal] = None
    currency: Optional[str] = None
    confirmed_by_id: Optional[uuid.UUID] = None
    confirmed_at: datetime
    notes: Optional[str] = None


class PartnerHistoryOut(BaseModel):
    partner: PartnerOut
    contacts: List[PartnerContactOut]
    collaborations: List[PartnerCollaborationOut]


class PartnerSearchResult(BaseModel):
    partner: PartnerOut
    already_contacted: bool
    last_contact: Optional[PartnerContactOut] = None
    previous_collaborations: List[PartnerCollaborationOut] = []
