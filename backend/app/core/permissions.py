"""Central permission matrix, matching the role/permission table from Phase 1.

This is deliberately a single dict, not scattered `if role == "ADMIN"` checks
across routers — adding a new action or changing who can do it means editing
one place. Entity-scoped nuance (e.g. an OCVP editing only THEIR department's
partners) is layered on top of this in the relevant service, since that
requires looking at the specific row, not just the actor's role.
"""
from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.enums import RoleEnum
from app.models.user import User


class Action(str, Enum):
    USER_MANAGE = "user:manage"  # create / edit / deactivate / assign role & manager

    PARTNER_CREATE = "partner:create"
    PARTNER_EDIT_OFFICIAL = "partner:edit_official"
    PARTNER_CHANGE_STATUS = "partner:change_status"
    PARTNER_CONTACT_LOG = "partner:contact_log"
    PARTNER_IMPORT = "partner:import"
    PARTNER_OVERRIDE_BLOCK = "partner:override_duplicate_block"

    TARGET_LIST_MANAGE = "target_list:manage"

    SPEAKER_MANAGE = "speaker:manage"
    SPEAKER_CONTACT_LOG = "speaker:contact_log"

    TASK_CREATE = "task:create"

    GOAL_MANAGE = "goal:manage"
    GOAL_VIEW = "goal:view"

    MKT_MANAGE = "mkt:manage"

    ACTIVITY_LOG_VIEW = "activity_log:view"
    ADMIN_DASHBOARD_VIEW = "admin_dashboard:view"
    PROJECT_DASHBOARD_VIEW = "project_dashboard:view"


PERMISSIONS: dict[RoleEnum, set[Action]] = {
    RoleEnum.ADMIN: set(Action),  # unrestricted
    RoleEnum.PM: {
        Action.TARGET_LIST_MANAGE,
        Action.PARTNER_CONTACT_LOG,
        Action.SPEAKER_MANAGE,
        Action.SPEAKER_CONTACT_LOG,
        Action.TASK_CREATE,
        Action.GOAL_MANAGE,
        Action.GOAL_VIEW,
        Action.MKT_MANAGE,
        Action.ACTIVITY_LOG_VIEW,
        Action.PROJECT_DASHBOARD_VIEW,
    },
    RoleEnum.OCP: {
        Action.TARGET_LIST_MANAGE,
        Action.PARTNER_CONTACT_LOG,
        Action.SPEAKER_MANAGE,
        Action.SPEAKER_CONTACT_LOG,
        Action.TASK_CREATE,
        Action.GOAL_VIEW,
        Action.MKT_MANAGE,
    },
    RoleEnum.OCVP: {
        Action.TARGET_LIST_MANAGE,
        Action.PARTNER_CONTACT_LOG,
        Action.PARTNER_EDIT_OFFICIAL,
        Action.PARTNER_CHANGE_STATUS,
        Action.SPEAKER_MANAGE,
        Action.SPEAKER_CONTACT_LOG,
        Action.TASK_CREATE,
        Action.GOAL_VIEW,
        Action.MKT_MANAGE,
    },
    RoleEnum.OC: {
        Action.TARGET_LIST_MANAGE,
        Action.PARTNER_CONTACT_LOG,
        Action.SPEAKER_CONTACT_LOG,
        Action.GOAL_VIEW,
    },
}


def has_permission(role: RoleEnum, action: Action) -> bool:
    return action in PERMISSIONS.get(role, set())


def require_permission(action: Action) -> Callable[..., User]:
    """FastAPI dependency factory: `Depends(require_permission(Action.X))`."""

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role ({current_user.role.value}) is not permitted to perform this action.",
            )
        return current_user

    return _dependency
