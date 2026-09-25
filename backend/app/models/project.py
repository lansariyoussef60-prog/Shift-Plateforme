import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Project(Base, TimestampMixin):
    """A project row (e.g. 'SHIFT'). The schema supports multiple projects from day
    one even though the beta only ever runs a single active project — this avoids a
    rebuild if AIESEC Bardo runs a second project on the same platform later."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    departments: Mapped[List["Department"]] = relationship("Department", back_populates="project")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
