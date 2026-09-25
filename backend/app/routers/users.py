import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import ManagerAssignment, UserCreate, UserOut
from app.services.user_service import UserServiceError, assign_manager, create_user, deactivate_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=List[UserOut])
def list_users(
    department_id: Optional[uuid.UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Beta rule: any authenticated user can list users (needed for task-assignee
    # pickers, "who contacted this partner", etc). Restricting *which* users a
    # given role should see by default is a Phase 4 UI/query-param concern
    # layered on this same endpoint, not a reason to hide the endpoint itself.
    return user_repository.list_users(db, department_id=department_id)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    try:
        return create_user(
            db,
            actor=current_user,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            department_id=payload.department_id,
            manager_id=payload.manager_id,
        )
    except UserServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{user_id}/manager", response_model=UserOut)
def assign_manager_endpoint(
    user_id: uuid.UUID,
    payload: ManagerAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    try:
        return assign_manager(db, actor=current_user, user_id=user_id, manager_id=payload.manager_id)
    except UserServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    try:
        return deactivate_user(db, actor=current_user, user_id=user_id)
    except UserServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
