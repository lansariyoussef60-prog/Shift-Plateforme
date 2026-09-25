import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import goal_repository
from app.schemas.goal import GoalCreate, GoalOut, GoalProgressUpdate
from app.services.goal_service import GoalServiceError, create_goal, update_progress

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=List[GoalOut])
def list_goals(
    project_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return goal_repository.list_for_project(db, project_id)


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal_endpoint(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.GOAL_MANAGE)),
):
    try:
        return create_goal(
            db,
            actor=current_user,
            title=payload.title,
            description=payload.description,
            target_value=payload.target_value,
            unit=payload.unit,
            scope=payload.scope,
            project_id=payload.project_id,
            department_id=payload.department_id,
            user_id=payload.user_id,
            responsible_id=payload.responsible_id,
            deadline=payload.deadline,
        )
    except GoalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{goal_id}/progress", response_model=GoalOut)
def update_goal_progress(
    goal_id: uuid.UUID,
    payload: GoalProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.GOAL_MANAGE)),
):
    try:
        return update_progress(db, actor=current_user, goal_id=goal_id, current_value=payload.current_value)
    except GoalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
