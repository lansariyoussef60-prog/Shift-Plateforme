import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Action, require_permission
from app.models.user import User
from app.schemas.dashboard import MyDashboardOut, ProjectDashboardOut, TeamDashboardOut
from app.services.dashboard_service import get_my_dashboard, get_project_dashboard, get_team_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me", response_model=MyDashboardOut)
def my_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_my_dashboard(db, current_user)


@router.get("/team", response_model=TeamDashboardOut)
def team_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # No permission gate: a user with zero direct reports just gets team_size=0.
    # This mirrors real org structure rather than hiding the route by role.
    return get_team_dashboard(db, current_user)


@router.get("/project", response_model=ProjectDashboardOut)
def project_dashboard(
    project_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.PROJECT_DASHBOARD_VIEW)),
):
    return get_project_dashboard(db, project_id)


@router.get("/admin", response_model=ProjectDashboardOut)
def admin_dashboard(
    project_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Action.ADMIN_DASHBOARD_VIEW)),
):
    return get_project_dashboard(db, project_id)
