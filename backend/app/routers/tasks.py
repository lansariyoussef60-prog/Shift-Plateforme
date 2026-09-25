import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import task_repository, user_repository
from app.schemas.task import TaskCounts, TaskCreate, TaskOut, TaskStatusUpdate
from app.services.task_service import (
    TaskPermissionError,
    TaskServiceError,
    create_task,
    get_task_counts_for_user,
    update_task_status,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskOut])
def list_tasks(
    scope: str = Query(default="mine", pattern="^(mine|created|team)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if scope == "mine":
        return task_repository.list_assigned_to(db, current_user.id)
    if scope == "created":
        return task_repository.list_created_by(db, current_user.id)
    # scope == "team": tasks assigned to the current user's direct reports.
    reports = user_repository.list_direct_reports(db, current_user.id)
    return task_repository.list_for_team(db, [r.id for r in reports])


@router.get("/counts/me", response_model=TaskCounts)
def my_task_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_task_counts_for_user(db, current_user.id)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.TASK_CREATE)),
):
    try:
        return create_task(
            db,
            actor=current_user,
            title=payload.title,
            description=payload.description,
            assigned_to_id=payload.assigned_to,
            priority=payload.priority,
            deadline=payload.deadline,
        )
    except TaskPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TaskServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status_endpoint(
    task_id: uuid.UUID,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_task_status(db, actor=current_user, task_id=task_id, new_status=payload.status)
    except TaskPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TaskServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
