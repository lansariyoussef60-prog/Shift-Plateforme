import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.partner import Partner
from app.models.speaker import Speaker
from app.models.task import Task
from app.models.user import User
from app.repositories import user_repository
from app.services.task_service import get_task_counts_for_user


def get_my_dashboard(db: Session, user: User) -> dict:
    return {"task_counts": get_task_counts_for_user(db, user.id)}


def get_team_dashboard(db: Session, manager: User) -> dict:
    reports = user_repository.list_direct_reports(db, manager.id)

    combined_counts = {"todo": 0, "in_progress": 0, "completed": 0, "overdue": 0, "cancelled": 0}
    for report in reports:
        counts = get_task_counts_for_user(db, report.id)
        for key in combined_counts:
            combined_counts[key] += counts[key]

    return {"team_size": len(reports), "task_counts": combined_counts}


def get_project_dashboard(db: Session, project_id: uuid.UUID) -> dict:
    """Every number here comes from a live COUNT/GROUP BY query — nothing is
    hardcoded or estimated. Note: task 'overdue' here reflects the stored
    OVERDUE status only (no background job flips TODO/IN_PROGRESS tasks past
    their deadline yet); /tasks/counts/me computes overdue dynamically from
    the deadline instead, which is why the two can disagree until a proper
    overdue-sweep job exists."""
    users_by_role_rows = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role.value: count for role, count in users_by_role_rows}
    total_users = sum(users_by_role.values())

    partner_rows = db.query(Partner.status, func.count(Partner.id)).group_by(Partner.status).all()
    partner_counts_raw = {status.value: count for status, count in partner_rows}
    partner_pipeline = {
        "new": partner_counts_raw.get("NEW", 0),
        "contacted": partner_counts_raw.get("CONTACTED", 0),
        "follow_up": partner_counts_raw.get("FOLLOW_UP", 0),
        "negotiation": partner_counts_raw.get("NEGOTIATION", 0),
        "signed": partner_counts_raw.get("SIGNED", 0),
        "rejected": partner_counts_raw.get("REJECTED", 0),
        "not_interested": partner_counts_raw.get("NOT_INTERESTED", 0),
    }

    speaker_rows = db.query(Speaker.status, func.count(Speaker.id)).group_by(Speaker.status).all()
    speaker_counts_raw = {status.value: count for status, count in speaker_rows}
    speaker_pipeline = {
        "prospect": speaker_counts_raw.get("PROSPECT", 0),
        "contacted": speaker_counts_raw.get("CONTACTED", 0),
        "interested": speaker_counts_raw.get("INTERESTED", 0),
        "confirmed": speaker_counts_raw.get("CONFIRMED", 0),
        "declined": speaker_counts_raw.get("DECLINED", 0),
        "follow_up": speaker_counts_raw.get("FOLLOW_UP", 0),
    }

    task_rows = db.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    task_counts_raw = {status.value: count for status, count in task_rows}
    task_counts = {
        "todo": task_counts_raw.get("TODO", 0),
        "in_progress": task_counts_raw.get("IN_PROGRESS", 0),
        "completed": task_counts_raw.get("COMPLETED", 0),
        "overdue": task_counts_raw.get("OVERDUE", 0),
        "cancelled": task_counts_raw.get("CANCELLED", 0),
    }

    return {
        "total_users": total_users,
        "users_by_role": users_by_role,
        "task_counts": task_counts,
        "partner_pipeline": partner_pipeline,
        "speaker_pipeline": speaker_pipeline,
    }
