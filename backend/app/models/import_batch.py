import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ImportBatchStatusEnum, ImportRowStatusEnum


class ImportBatch(Base):
    """One row per uploaded file. Counts are computed during validation and shown
    to the Admin as the 'Import Preview' before anything is committed."""

    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ImportBatchStatusEnum] = mapped_column(
        SAEnum(ImportBatchStatusEnum, name="import_batch_status_enum"),
        nullable=False,
        default=ImportBatchStatusEnum.PENDING,
    )

    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uploaded_by: Mapped[Optional["User"]] = relationship("User")
    rows: Mapped[List["ImportRow"]] = relationship(
        "ImportRow", back_populates="import_batch", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ImportBatch {self.file_name} ({self.status})>"


class ImportRow(Base):
    """One row per spreadsheet line. raw_data preserves the original parsed row so
    the Admin's preview can show exactly what will be created, and so failed rows
    can be corrected and re-submitted without re-uploading the whole file."""

    __tablename__ = "import_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )

    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    row_status: Mapped[ImportRowStatusEnum] = mapped_column(
        SAEnum(ImportRowStatusEnum, name="import_row_status_enum"), nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_partner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="SET NULL"), nullable=True
    )

    import_batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="rows")
    resolved_partner: Mapped[Optional["Partner"]] = relationship("Partner")

    def __repr__(self) -> str:
        return f"<ImportRow batch={self.import_batch_id} status={self.row_status}>"
