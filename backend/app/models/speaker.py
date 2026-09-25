import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import SpeakerStatusEnum


class Speaker(Base, TimestampMixin):
    """Mirrors the Partner model's duplicate-detection design: normalized_name is
    UNIQUE so the same speaker can't be silently re-added as a fresh prospect by a
    different member."""

    __tablename__ = "speakers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    organization: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linkedin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[SpeakerStatusEnum] = mapped_column(
        SAEnum(SpeakerStatusEnum, name="speaker_status_enum"), nullable=False, default=SpeakerStatusEnum.PROSPECT
    )
    contacted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    contact_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confirmation_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contacted_by: Mapped[Optional["User"]] = relationship("User")
    contacts: Mapped[List["SpeakerContact"]] = relationship(
        "SpeakerContact", back_populates="speaker", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Speaker {self.name} ({self.status})>"
