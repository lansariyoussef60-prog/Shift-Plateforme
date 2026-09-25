import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import GoalScopeEnum, GoalStatusEnum


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    target_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    scope: Mapped[GoalScopeEnum] = mapped_column(SAEnum(GoalScopeEnum, name="goal_scope_enum"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    responsible_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatusEnum] = mapped_column(
        SAEnum(GoalStatusEnum, name="goal_status_enum"), nullable=False, default=GoalStatusEnum.ON_TRACK
    )

    project: Mapped["Project"] = relationship("Project")
    department: Mapped[Optional["Department"]] = relationship("Department")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    responsible: Mapped[Optional["User"]] = relationship("User", foreign_keys=[responsible_id])

    def __repr__(self) -> str:
        return f"<Goal {self.title} {self.current_value}/{self.target_value}{self.unit or ''}>"
