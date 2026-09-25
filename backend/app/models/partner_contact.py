import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ContactMethodEnum


class PartnerContact(Base, TimestampMixin):
    """Append-only interaction log. The service layer never exposes an update/delete
    endpoint for this table — corrections are made by adding a new row, so the
    history a manager sees is always exactly what happened, in order."""

    __tablename__ = "partner_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    contact_method: Mapped[ContactMethodEnum] = mapped_column(
        SAEnum(ContactMethodEnum, name="contact_method_enum"), nullable=False
    )
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    partner: Mapped["Partner"] = relationship("Partner", back_populates="contacts")
    user: Mapped[Optional["User"]] = relationship("User")
    project: Mapped[Optional["Project"]] = relationship("Project")

    def __repr__(self) -> str:
        return f"<PartnerContact partner={self.partner_id} by={self.user_id}>"
