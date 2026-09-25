import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TargetListItemStatusEnum
from app.schemas.partner import PartnerContactOut, PartnerOut


class TargetListCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    department_id: Optional[uuid.UUID] = None
    project_id: uuid.UUID


class TargetListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    project_id: uuid.UUID
    created_at: datetime


class TargetListItemCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    # Only ever honored server-side if the actor's role actually carries the
    # PARTNER_OVERRIDE_BLOCK permission (Admin, in the beta) — see the router.
    override_duplicate_block: bool = False


class TargetListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_list_id: uuid.UUID
    partner_id: uuid.UUID
    status: TargetListItemStatusEnum
    added_by_id: Optional[uuid.UUID] = None
    added_at: datetime
    partner: PartnerOut


class TargetListItemStatusUpdate(BaseModel):
    status: TargetListItemStatusEnum


class AlreadyContactedDetail(BaseModel):
    """Shape of the 409 response body when the duplicate-contact block fires —
    matches the spec's 'Already Contacted' warning panel exactly."""

    message: str
    partner: PartnerOut
    last_contact: Optional[PartnerContactOut] = None
