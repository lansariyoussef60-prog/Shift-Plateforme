import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import MktStatusEnum, TaskPriorityEnum


class MktTimelineItem(Base, TimestampMixin):
    __tablename__ = "mkt_timeline_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    responsible_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[MktStatusEnum] = mapped_column(
        SAEnum(MktStatusEnum, name="mkt_status_enum"), nullable=False, default=MktStatusEnum.PLANNED
    )
    priority: Mapped[TaskPriorityEnum] = mapped_column(
        SAEnum(TaskPriorityEnum, name="task_priority_enum"), nullable=False, default=TaskPriorityEnum.MEDIUM
    )

    related_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    responsible: Mapped[Optional["User"]] = relationship("User")
    department: Mapped[Optional["Department"]] = relationship("Department")
    project: Mapped["Project"] = relationship("Project")
    related_task: Mapped[Optional["Task"]] = relationship("Task")

    def __repr__(self) -> str:
        return f"<MktTimelineItem {self.title} ({self.status})>"
