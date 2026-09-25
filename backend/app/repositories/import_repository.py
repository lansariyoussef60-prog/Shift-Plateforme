import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.import_batch import ImportBatch, ImportRow


def create_batch(db: Session, batch: ImportBatch) -> ImportBatch:
    db.add(batch)
    db.flush()
    return batch


def create_row(db: Session, row: ImportRow) -> ImportRow:
    db.add(row)
    db.flush()
    return row


def get_batch(db: Session, batch_id: uuid.UUID) -> Optional[ImportBatch]:
    return (
        db.query(ImportBatch)
        .options(joinedload(ImportBatch.rows))
        .filter(ImportBatch.id == batch_id)
        .first()
    )


def list_batches(db: Session, limit: int = 50) -> List[ImportBatch]:
    return db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(limit).all()
