import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import mkt_timeline_repository
from app.schemas.mkt_timeline import MktTimelineItemCreate, MktTimelineItemOut, MktTimelineItemStatusUpdate
from app.services.mkt_timeline_service import MktTimelineServiceError, create_item, update_status

router = APIRouter(prefix="/mkt-timeline", tags=["mkt-timeline"])


@router.get("", response_model=List[MktTimelineItemOut])
def list_timeline(
    project_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return mkt_timeline_repository.list_for_project(db, project_id)


@router.post("", response_model=MktTimelineItemOut, status_code=status.HTTP_201_CREATED)
def create_timeline_item(
    payload: MktTimelineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.MKT_MANAGE)),
):
    try:
        return create_item(
            db,
            actor=current_user,
            title=payload.title,
            description=payload.description,
            start_date=payload.start_date,
            end_date=payload.end_date,
            responsible_id=payload.responsible_id,
            department_id=payload.department_id,
            project_id=payload.project_id,
            priority=payload.priority,
            related_task_id=payload.related_task_id,
            notes=payload.notes,
        )
    except MktTimelineServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{item_id}/status", response_model=MktTimelineItemOut)
def update_timeline_item_status(
    item_id: uuid.UUID,
    payload: MktTimelineItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.MKT_MANAGE)),
):
    try:
        return update_status(db, actor=current_user, item_id=item_id, new_status=payload.status)
    except MktTimelineServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
