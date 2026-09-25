import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriorityEnum, TaskStatusEnum


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    assigned_to: uuid.UUID
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    deadline: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatusEnum


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    created_by_id: Optional[uuid.UUID] = None
    assigned_to_id: uuid.UUID
    priority: TaskPriorityEnum
    status: TaskStatusEnum
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TaskCounts(BaseModel):
    todo: int
    in_progress: int
    completed: int
    overdue: int
    cancelled: int
