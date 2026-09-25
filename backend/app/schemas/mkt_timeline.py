import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MktStatusEnum, TaskPriorityEnum


class MktTimelineItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    responsible_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    project_id: uuid.UUID
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    related_task_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class MktTimelineItemStatusUpdate(BaseModel):
    status: MktStatusEnum


class MktTimelineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    responsible_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    project_id: uuid.UUID
    status: MktStatusEnum
    priority: TaskPriorityEnum
    related_task_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
