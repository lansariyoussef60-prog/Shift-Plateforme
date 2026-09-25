from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import Action, require_permission
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.activity_log import ActivityLogOut

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@router.get("", response_model=List[ActivityLogOut])
def list_activity_logs(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.ACTIVITY_LOG_VIEW)),
):
    return db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).all()
