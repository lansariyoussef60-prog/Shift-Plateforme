import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, has_permission
from app.models.user import User
from app.repositories import target_list_repository
from app.schemas.partner import PartnerContactOut, PartnerOut
from app.schemas.target_list import (
    AlreadyContactedDetail,
    TargetListCreate,
    TargetListItemCreate,
    TargetListItemOut,
    TargetListItemStatusUpdate,
    TargetListOut,
)
from app.services.partner_service import DuplicatePartnerBlockedError
from app.services.target_list_service import (
    TargetListServiceError,
    add_item,
    create_target_list,
    update_item_status,
)

router = APIRouter(prefix="/target-lists", tags=["target-lists"])


@router.get("", response_model=List[TargetListOut])
def list_target_lists(
    mine_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_id = current_user.id if mine_only else None
    return target_list_repository.list_for_user(db, owner_id=owner_id)


@router.post("", response_model=TargetListOut, status_code=status.HTTP_201_CREATED)
def create_target_list_endpoint(
    payload: TargetListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_target_list(
        db,
        actor=current_user,
        name=payload.name,
        department_id=payload.department_id,
        project_id=payload.project_id,
    )


@router.get("/{target_list_id}", response_model=TargetListOut)
def get_target_list(
    target_list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_list = target_list_repository.get_by_id(db, target_list_id)
    if target_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target list not found.")
    return target_list


@router.get("/{target_list_id}/items", response_model=List[TargetListItemOut])
def list_target_list_items(
    target_list_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return target_list_repository.list_items(db, target_list_id)


@router.post(
    "/{target_list_id}/items", response_model=TargetListItemOut, status_code=status.HTTP_201_CREATED
)
def add_target_list_item(
    target_list_id: uuid.UUID,
    payload: TargetListItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """This is the endpoint from spec sections 14/16: search -> already
    contacted? -> block, or create + add. The override flag in the request
    body is only ever honored if the ACTOR'S ROLE carries
    PARTNER_OVERRIDE_BLOCK — a non-admin sending override_duplicate_block=true
    has no effect, because allow_override is computed from the server-side
    permission check, not trusted from the payload."""
    allow_override = payload.override_duplicate_block and has_permission(
        current_user.role, Action.PARTNER_OVERRIDE_BLOCK
    )

    try:
        return add_item(
            db,
            actor=current_user,
            target_list_id=target_list_id,
            company_name=payload.company_name,
            allow_override=allow_override,
        )
    except DuplicatePartnerBlockedError as exc:
        detail = AlreadyContactedDetail(
            message=(
                f"{exc.partner.company_name} has already been contacted. "
                "Adding it as a new prospect is blocked."
            ),
            partner=PartnerOut.model_validate(exc.partner),
            last_contact=PartnerContactOut.model_validate(exc.latest_contact) if exc.latest_contact else None,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail.model_dump(mode="json"))
    except TargetListServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/items/{item_id}/status", response_model=TargetListItemOut)
def update_target_list_item_status(
    item_id: uuid.UUID,
    payload: TargetListItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_item_status(db, actor=current_user, item_id=item_id, new_status=payload.status)
    except TargetListServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
