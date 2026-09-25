from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.repositories import user_repository


class AuthError(ValueError):
    pass


def authenticate(db: Session, email: str, password: str) -> User:
    user = user_repository.get_by_email(db, email.strip().lower())
    if user is None or not verify_password(password, user.password_hash):
        # Deliberately identical message for "no such user" and "wrong password"
        # so login can't be used to enumerate valid email addresses.
        raise AuthError("Incorrect email or password.")
    if not user.is_active:
        raise AuthError("This account has been deactivated.")
    return user


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
        "token_type": "bearer",
    }
