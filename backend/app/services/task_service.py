import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, TaskPriorityEnum, TaskStatusEnum
from app.models.task import Task
from app.models.user import User
from app.repositories import task_repository, user_repository
from app.services.activity_log_service import log_activity
from app.services.hierarchy_service import is_direct_report


class TaskServiceError(ValueError):
    """Raised for ordinary business-rule violations (missing assignee) -> 400/404."""


class TaskPermissionError(ValueError):
    """Raised specifically for hierarchy violations (spec scenario 6: 'OC tries
    to assign task to another OCVP' -> Forbidden) so the router returns 403,
    not 400."""


def create_task(
    db: Session,
    *,
    actor: User,
    title: str,
    description: Optional[str],
    assigned_to_id: uuid.UUID,
    priority: TaskPriorityEnum,
    deadline: Optional[datetime],
) -> Task:
    assignee = user_repository.get_by_id(db, assigned_to_id)
    if assignee is None:
        raise TaskServiceError("Assignee not found.")

    # Admin can assign to anyone (global override, logged like any admin
    # action). Every other role must be assigning strictly one level down the
    # PM -> OCP -> OCVP -> OC chain — this is spec scenario 5 (OCP -> OCVP:
    # allowed) vs scenario 6 (OC -> another OCVP: forbidden).
    if actor.role != RoleEnum.ADMIN and not is_direct_report(actor, assignee):
        raise TaskPermissionError(
            f"You can only assign tasks to your direct reports. {assignee.full_name} does not report to you."
        )

    task = Task(
        title=title.strip(),
        description=description,
        created_by_id=actor.id,
        assigned_to_id=assignee.id,
        priority=priority,
        status=TaskStatusEnum.TODO,
        deadline=deadline,
    )
    task_repository.create(db, task)
    db.commit()
    db.refresh(task)

    log_activity(
        db,
        actor=actor,
        action="TASK_ASSIGNED",
        entity_type="Task",
        entity_id=task.id,
        description=f"{actor.full_name} assigned task '{task.title}' to {assignee.full_name}.",
    )
    db.commit()
    return task


def update_task_status(db: Session, *, actor: User, task_id: uuid.UUID, new_status: TaskStatusEnum) -> Task:
    task = task_repository.get_by_id(db, task_id)
    if task is None:
        raise TaskServiceError("Task not found.")

    # Only the assignee (or an Admin) can move a task's status — a manager can
    # create and monitor a task but shouldn't be able to mark someone else's
    # work "done" for them.
    if actor.role != RoleEnum.ADMIN and task.assigned_to_id != actor.id:
        raise TaskPermissionError("Only the assignee (or an Admin) can update this task's status.")

    old_status = task.status
    task.status = new_status
    if new_status == TaskStatusEnum.COMPLETED:
        task.completed_at = task.completed_at or datetime.now(timezone.utc)
    else:
        task.completed_at = None

    db.commit()
    db.refresh(task)

    log_activity(
        db,
        actor=actor,
        action="TASK_STATUS_CHANGED",
        entity_type="Task",
        entity_id=task.id,
        description=(
            f"{actor.full_name} changed task '{task.title}' status "
            f"from {old_status.value} to {new_status.value}."
        ),
    )
    db.commit()
    return task


def get_task_counts_for_user(db: Session, user_id: uuid.UUID) -> dict:
    tasks = task_repository.list_assigned_to(db, user_id)
    counts = {"todo": 0, "in_progress": 0, "completed": 0, "overdue": 0, "cancelled": 0}
    now = datetime.now(timezone.utc)

    for task in tasks:
        is_late = task.deadline is not None and task.deadline < now
        if task.status in (TaskStatusEnum.TODO, TaskStatusEnum.IN_PROGRESS) and is_late:
            counts["overdue"] += 1
        elif task.status == TaskStatusEnum.TODO:
            counts["todo"] += 1
        elif task.status == TaskStatusEnum.IN_PROGRESS:
            counts["in_progress"] += 1
        elif task.status == TaskStatusEnum.COMPLETED:
            counts["completed"] += 1
        elif task.status == TaskStatusEnum.OVERDUE:
            counts["overdue"] += 1
        elif task.status == TaskStatusEnum.CANCELLED:
            counts["cancelled"] += 1

    return counts
