import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.repositories import partner_repository
from app.schemas.partner import (
    PartnerCollaborationCreate,
    PartnerCollaborationOut,
    PartnerContactCreate,
    PartnerContactOut,
    PartnerCreate,
    PartnerHistoryOut,
    PartnerOut,
    PartnerSearchResult,
    PartnerStatusUpdate,
    PartnerUpdate,
)
from app.services import partner_service
from app.services.partner_service import PartnerServiceError

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("", response_model=List[PartnerOut])
def list_partners(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return partner_repository.list_all(db, limit=limit, offset=offset)


@router.get("/search", response_model=List[PartnerSearchResult])
def search_partners(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Powers the target-list search flow: for each match, tells the caller
    up front whether it's already contacted and by whom, so the UI can show
    the warning before the user even tries to add it."""
    results = []
    for partner in partner_service.search_partners(db, q):
        latest_contact = partner_repository.get_latest_contact(db, partner.id)
        collaborations = partner_repository.list_collaborations(db, partner.id)
        results.append(
            PartnerSearchResult(
                partner=PartnerOut.model_validate(partner),
                already_contacted=partner.status.value != "NEW",
                last_contact=PartnerContactOut.model_validate(latest_contact) if latest_contact else None,
                previous_collaborations=[
                    PartnerCollaborationOut.model_validate(c) for c in collaborations
                ],
            )
        )
    return results


@router.post("", response_model=PartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner_endpoint(
    payload: PartnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_CREATE)),
):
    try:
        return partner_service.create_partner(
            db,
            actor=current_user,
            company_name=payload.company_name,
            industry=payload.industry,
            contact_person=payload.contact_person,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            city=payload.city,
            website=payload.website,
            partner_type=payload.partner_type,
            notes=payload.notes,
        )
    except PartnerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{partner_id}", response_model=PartnerOut)
def get_partner(
    partner_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = partner_repository.get_by_id(db, partner_id)
    if partner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found.")
    return partner


@router.get("/{partner_id}/history", response_model=PartnerHistoryOut)
def get_partner_history(
    partner_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = partner_repository.get_by_id(db, partner_id)
    if partner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found.")
    return PartnerHistoryOut(
        partner=PartnerOut.model_validate(partner),
        contacts=[
            PartnerContactOut.model_validate(c) for c in partner_repository.list_contacts(db, partner_id)
        ],
        collaborations=[
            PartnerCollaborationOut.model_validate(c)
            for c in partner_repository.list_collaborations(db, partner_id)
        ],
    )


@router.put("/{partner_id}", response_model=PartnerOut)
def update_partner(
    partner_id: uuid.UUID,
    payload: PartnerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_EDIT_OFFICIAL)),
):
    try:
        return partner_service.update_official_fields(
            db, actor=current_user, partner_id=partner_id, updates=payload.model_dump(exclude_unset=True)
        )
    except PartnerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{partner_id}/status", response_model=PartnerOut)
def change_partner_status(
    partner_id: uuid.UUID,
    payload: PartnerStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_CHANGE_STATUS)),
):
    try:
        return partner_service.change_status(
            db, actor=current_user, partner_id=partner_id, new_status=payload.status
        )
    except PartnerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{partner_id}/contacts", response_model=PartnerContactOut, status_code=status.HTTP_201_CREATED
)
def add_partner_contact(
    partner_id: uuid.UUID,
    payload: PartnerContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_CONTACT_LOG)),
):
    try:
        return partner_service.add_contact(
            db,
            actor=current_user,
            partner_id=partner_id,
            contact_method=payload.contact_method,
            result=payload.result,
            notes=payload.notes,
            follow_up_date=payload.follow_up_date,
            project_id=payload.project_id,
        )
    except PartnerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{partner_id}/collaborations",
    response_model=PartnerCollaborationOut,
    status_code=status.HTTP_201_CREATED,
)
def add_partner_collaboration(
    partner_id: uuid.UUID,
    payload: PartnerCollaborationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PARTNER_EDIT_OFFICIAL)),
):
    try:
        return partner_service.add_collaboration(
            db,
            actor=current_user,
            partner_id=partner_id,
            project_id=payload.project_id,
            title=payload.title,
            amount_value=payload.amount_value,
            currency=payload.currency,
            notes=payload.notes,
        )
    except PartnerServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
