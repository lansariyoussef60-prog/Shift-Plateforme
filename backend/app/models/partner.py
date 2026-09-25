import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import PartnerStatusEnum, PartnerTypeEnum


class Partner(Base, TimestampMixin):
    """The single centralized partner record. normalized_name is UNIQUE and is what
    the duplicate-detection / "already contacted" logic keys off — it is a
    lowercased, trimmed, punctuation-stripped version of company_name computed by
    the service layer on write, never edited directly."""

    __tablename__ = "partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    industry: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    social_media: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded string (beta-simple)

    partner_type: Mapped[PartnerTypeEnum] = mapped_column(
        SAEnum(PartnerTypeEnum, name="partner_type_enum"), nullable=False, default=PartnerTypeEnum.OTHER
    )
    status: Mapped[PartnerStatusEnum] = mapped_column(
        SAEnum(PartnerStatusEnum, name="partner_status_enum"), nullable=False, default=PartnerStatusEnum.NEW
    )

    # Denormalized for fast duplicate-detection lookups; kept in sync by the service
    # layer whenever a new PartnerContact is recorded.
    last_contact_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_contacted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    last_contacted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[last_contacted_by_id])
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])

    contacts: Mapped[List["PartnerContact"]] = relationship(
        "PartnerContact", back_populates="partner", cascade="all, delete-orphan"
    )
    collaborations: Mapped[List["PartnerCollaboration"]] = relationship(
        "PartnerCollaboration", back_populates="partner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Partner {self.company_name} ({self.status})>"
