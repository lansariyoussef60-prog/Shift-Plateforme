import uuid
from datetime import date as date_cls
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import GoalScopeEnum, GoalStatusEnum
from app.models.goal import Goal
from app.models.user import User
from app.repositories import goal_repository
from app.services.activity_log_service import log_activity


class GoalServiceError(ValueError):
    pass


def _derive_status(current_value: Decimal, target_value: Decimal, deadline: Optional[date_cls]) -> GoalStatusEnum:
    """Status is derived from real numbers, not set arbitrarily: hitting the
    target means ACHIEVED regardless of date; missing the deadline while still
    short means MISSED; otherwise it's ON_TRACK. (AT_RISK is reserved for a
    future, more precise pace-based calculation once there's real historical
    data to compare against — the beta doesn't fabricate that signal.)"""
    if current_value >= target_value:
        return GoalStatusEnum.ACHIEVED
    if deadline is not None and deadline < date_cls.today():
        return GoalStatusEnum.MISSED
    return GoalStatusEnum.ON_TRACK


def create_goal(
    db: Session,
    *,
    actor: User,
    title: str,
    description: Optional[str],
    target_value: Decimal,
    unit: Optional[str],
    scope: GoalScopeEnum,
    project_id: uuid.UUID,
    department_id: Optional[uuid.UUID],
    user_id: Optional[uuid.UUID],
    responsible_id: Optional[uuid.UUID],
    deadline: Optional[date_cls],
) -> Goal:
    if scope == GoalScopeEnum.DEPARTMENT and department_id is None:
        raise GoalServiceError("A department-scoped goal requires department_id.")
    if scope == GoalScopeEnum.INDIVIDUAL and user_id is None:
        raise GoalServiceError("An individual-scoped goal requires user_id.")

    goal = Goal(
        title=title.strip(),
        description=description,
        target_value=target_value,
        current_value=Decimal("0"),
        unit=unit,
        scope=scope,
        project_id=project_id,
        department_id=department_id,
        user_id=user_id,
        responsible_id=responsible_id,
        deadline=deadline,
        status=GoalStatusEnum.ON_TRACK,
    )
    goal_repository.create(db, goal)
    db.commit()
    db.refresh(goal)

    log_activity(
        db,
        actor=actor,
        action="GOAL_CREATED",
        entity_type="Goal",
        entity_id=goal.id,
        description=f"{actor.full_name} created goal '{goal.title}' (target {goal.target_value}{goal.unit or ''}).",
    )
    db.commit()
    return goal


def update_progress(db: Session, *, actor: User, goal_id: uuid.UUID, current_value: Decimal) -> Goal:
    goal = goal_repository.get_by_id(db, goal_id)
    if goal is None:
        raise GoalServiceError("Goal not found.")

    goal.current_value = current_value
    goal.status = _derive_status(current_value, goal.target_value, goal.deadline)
    db.commit()
    db.refresh(goal)

    log_activity(
        db,
        actor=actor,
        action="GOAL_PROGRESS_UPDATED",
        entity_type="Goal",
        entity_id=goal.id,
        description=f"{actor.full_name} updated '{goal.title}' progress to {current_value}{goal.unit or ''}.",
    )
    db.commit()
    return goal
