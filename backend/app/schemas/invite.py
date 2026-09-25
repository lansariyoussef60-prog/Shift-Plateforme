import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleEnum


class InviteCreate(BaseModel):
    email: EmailStr
    role: RoleEnum
    department_id: Optional[uuid.UUID] = None
    manager_id: Optional[uuid.UUID] = None


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: RoleEnum
    department_id: Optional[uuid.UUID] = None
    manager_id: Optional[uuid.UUID] = None
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime
    invite_link: Optional[str] = None  # only populated right after creation


class RegisterWithInviteRequest(BaseModel):
    token: str
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=72)