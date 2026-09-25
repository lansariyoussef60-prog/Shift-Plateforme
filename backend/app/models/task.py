import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import TaskPriorityEnum, TaskStatusEnum


class Task(Base, TimestampMixin):
    """assigned_to is always a direct report of created_by (enforced in the service
    layer, not here) — one level down the hierarchy, never sideways or skipping a
    level."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    priority: Mapped[TaskPriorityEnum] = mapped_column(
        SAEnum(TaskPriorityEnum, name="task_priority_enum"), nullable=False, default=TaskPriorityEnum.MEDIUM
    )
    status: Mapped[TaskStatusEnum] = mapped_column(
        SAEnum(TaskStatusEnum, name="task_status_enum"), nullable=False, default=TaskStatusEnum.TODO
    )

    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_id])

    def __repr__(self) -> str:
        return f"<Task {self.title} ({self.status})>"
