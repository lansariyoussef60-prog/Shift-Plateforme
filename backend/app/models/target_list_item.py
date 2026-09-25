import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TargetListItemStatusEnum


class TargetListItem(Base):
    """A single prospect line inside a TargetList. The UNIQUE constraint below
    prevents the same partner being added twice to the same list; the
    'already contacted' block itself is enforced in the service layer against the
    Partner's global status, not here — this table only records what is IN the
    list, not whether it was allowed to be added."""

    __tablename__ = "target_list_items"
    __table_args__ = (
        UniqueConstraint("target_list_id", "partner_id", name="uq_target_list_partner"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_lists.id", ondelete="CASCADE"), nullable=False
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[TargetListItemStatusEnum] = mapped_column(
        SAEnum(TargetListItemStatusEnum, name="target_list_item_status_enum"),
        nullable=False,
        default=TargetListItemStatusEnum.PROSPECT,
    )
    added_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    target_list: Mapped["TargetList"] = relationship("TargetList", back_populates="items")
    partner: Mapped["Partner"] = relationship("Partner")
    added_by: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<TargetListItem list={self.target_list_id} partner={self.partner_id}>"
