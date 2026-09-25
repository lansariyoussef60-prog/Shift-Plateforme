import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GoalScopeEnum, GoalStatusEnum


class GoalCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    target_value: Decimal
    unit: Optional[str] = None
    scope: GoalScopeEnum
    project_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    responsible_id: Optional[uuid.UUID] = None
    deadline: Optional[date] = None


class GoalProgressUpdate(BaseModel):
    current_value: Decimal


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    target_value: Decimal
    current_value: Decimal
    unit: Optional[str] = None
    scope: GoalScopeEnum
    project_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    responsible_id: Optional[uuid.UUID] = None
    deadline: Optional[date] = None
    status: GoalStatusEnum
    created_at: datetime
    updated_at: datetime
