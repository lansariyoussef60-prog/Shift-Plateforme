import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportBatchStatusEnum, ImportRowStatusEnum


class ImportRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    raw_data: Dict[str, Any]
    row_status: ImportRowStatusEnum
    error_message: Optional[str] = None
    resolved_partner_id: Optional[uuid.UUID] = None


class ImportBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    status: ImportBatchStatusEnum
    total_rows: int
    new_count: int
    duplicate_count: int
    error_count: int
    created_at: datetime


class ImportPreviewOut(ImportBatchOut):
    rows: List[ImportRowOut]
