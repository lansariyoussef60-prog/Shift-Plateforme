import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PartnerCollaboration(Base):
    """Official, manager/admin-confirmed collaborations (past or current). Kept
    separate from PartnerContact because it represents a confirmed business outcome
    ('Youth Speak 2026', a signed sponsorship amount) rather than a raw interaction,
    and only authorized roles can write to this table."""

    __tablename__ = "partner_collaborations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="TND")

    confirmed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    partner: Mapped["Partner"] = relationship("Partner", back_populates="collaborations")
    project: Mapped["Project"] = relationship("Project")
    confirmed_by: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<PartnerCollaboration {self.title}>"
