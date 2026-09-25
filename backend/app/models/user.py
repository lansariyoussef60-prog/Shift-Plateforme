import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import RoleEnum


class User(Base, TimestampMixin):
    """A platform user. manager_id is a self-referencing FK that encodes the entire
    PM -> OCP -> OCVP -> OC reporting hierarchy without a separate table — the
    hierarchy is always exactly as deep as the org actually is, and is built
    entirely by the Admin through the UI, never hardcoded."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum, name="role_enum"), nullable=False)

    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="members", foreign_keys=[department_id]
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User", remote_side=[id], back_populates="direct_reports"
    )
    direct_reports: Mapped[List["User"]] = relationship("User", back_populates="manager")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
