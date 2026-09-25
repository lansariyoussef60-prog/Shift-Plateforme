from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.project import Project
from app.models.user import User
from app.repositories import project_repository
from app.schemas.project import ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return project_repository.list_all(db)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    # Reuses the broadest existing permission (Admin-only) rather than adding
    # a dedicated action for what's a rare, low-volume operation in the beta.
    current_user: User = Depends(require_permission(Action.USER_MANAGE)),
):
    project = Project(name=payload.name.strip(), start_date=payload.start_date, end_date=payload.end_date)
    try:
        project_repository.create(db, project)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"A project named '{payload.name}' already exists."
        )
    db.refresh(project)
    return project
