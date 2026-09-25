import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleEnum


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    role: RoleEnum
    department_id: Optional[uuid.UUID] = None
    manager_id: Optional[uuid.UUID] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class ManagerAssignment(BaseModel):
    manager_id: Optional[uuid.UUID] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: RoleEnum
    department_id: Optional[uuid.UUID] = None
    manager_id: Optional[uuid.UUID] = None
    is_active: bool
