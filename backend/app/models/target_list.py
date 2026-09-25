import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TargetList(Base, TimestampMixin):
    """A prospecting list owned by a member. Its items always point back to the
    centralized Partner table — a target list never stores its own copy of a
    company's data."""

    __tablename__ = "target_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    owner: Mapped["User"] = relationship("User")
    department: Mapped[Optional["Department"]] = relationship("Department")
    project: Mapped["Project"] = relationship("Project")
    items: Mapped[List["TargetListItem"]] = relationship(
        "TargetListItem", back_populates="target_list", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TargetList {self.name}>"
