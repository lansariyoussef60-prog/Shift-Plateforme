import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import invite_repository
from app.schemas.invite import InviteCreate, InviteOut
from app.services.invite_service import InviteServiceError, create_invite, revoke_invite

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("", response_model=List[InviteOut])
def list_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    return invite_repository.list_all(db)


@router.post("", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def create_invite_endpoint(
    payload: InviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    try:
        invite = create_invite(
            db,
            actor=current_user,
            email=payload.email,
            role=payload.role,
            department_id=payload.department_id,
            manager_id=payload.manager_id,
        )
    except InviteServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    result = InviteOut.model_validate(invite)
    result.invite_link = f"{settings.FRONTEND_BASE_URL}/register?token={invite.token}"
    return result


@router.delete("/{invite_id}", response_model=InviteOut)
def revoke_invite_endpoint(
    invite_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    try:
        return revoke_invite(db, actor=current_user, invite_id=invite_id)
    except InviteServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))