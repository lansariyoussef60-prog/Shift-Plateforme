"""Encodes the PM -> OCP -> OCVP -> OC reporting chain as data, not as scattered
if-statements. This is the single place that decides whether a manager/role
pairing is legal — used both when creating a user and when re-assigning a
manager, and reused later by the task-assignment service (a task's assignee
must be a direct report of its creator)."""
from typing import Optional

from app.models.enums import RoleEnum
from app.models.user import User

# The role a user's manager MUST hold, keyed by the user's own role.
# None means "this role has no manager" (PM sits at the top of the project
# hierarchy; ADMIN sits outside it entirely).
REQUIRED_MANAGER_ROLE: dict[RoleEnum, Optional[RoleEnum]] = {
    RoleEnum.ADMIN: None,
    RoleEnum.PM: None,
    RoleEnum.OCP: RoleEnum.PM,
    RoleEnum.OCVP: RoleEnum.OCP,
    RoleEnum.OC: RoleEnum.OCVP,
}


class HierarchyError(ValueError):
    """Raised when a proposed manager/role pairing violates the SHIFT hierarchy."""


def validate_manager_assignment(user_role: RoleEnum, manager: Optional[User]) -> None:
    required_role = REQUIRED_MANAGER_ROLE[user_role]

    if required_role is None:
        if manager is not None:
            raise HierarchyError(f"A user with role {user_role.value} cannot have a manager.")
        return

    if manager is None:
        raise HierarchyError(
            f"A user with role {user_role.value} must have a manager with role {required_role.value}."
        )

    if manager.role != required_role:
        raise HierarchyError(
            f"A user with role {user_role.value} must report to a {required_role.value}, "
            f"not a {manager.role.value}."
        )


def is_direct_report(potential_manager: User, potential_report: User) -> bool:
    """True if potential_report reports directly to potential_manager. This is the
    rule enforced everywhere a manager acts on 'their own' people — most
    importantly, task assignment must only ever go one level down."""
    return potential_report.manager_id == potential_manager.id
