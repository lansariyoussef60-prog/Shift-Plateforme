from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_token
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.invite import RegisterWithInviteRequest
from app.services.auth_service import AuthError, authenticate, issue_tokens
from app.services.invite_service import InviteServiceError, register_with_invite

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate(db, payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return issue_tokens(user)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterWithInviteRequest, db: Session = Depends(get_db)):
    """Public endpoint — no auth required, since this IS how someone gets
    their first token. Only reachable with a valid, unused, unexpired invite
    token; the role/manager/department all come from the invite, never from
    this request body."""
    try:
        user = register_with_invite(
            db, token=payload.token, full_name=payload.full_name, password=payload.password
        )
    except InviteServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest):
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token."
        )
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token.")

    new_access_token = create_access_token(subject=claims["sub"])
    return {"access_token": new_access_token, "refresh_token": payload.refresh_token, "token_type": "bearer"}