import uuid
from typing import List

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Department(Base, TimestampMixin):
    """Departments (BD, MKT, Logistics, ...) are seeded for the beta but remain fully
    editable by the Admin — they are data, never hardcoded in application logic."""

    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_department_project_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="departments")
    members: Mapped[List["User"]] = relationship(
        "User", back_populates="department", foreign_keys="User.department_id"
    )

    def __repr__(self) -> str:
        return f"<Department {self.name}>"
