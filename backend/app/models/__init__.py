"""Importing this package registers every ORM model on Base.metadata.
Alembic's env.py relies on this for autogeneration and metadata inspection.
"""
from app.models.user import User
from app.models.department import Department
from app.models.project import Project
from app.models.partner import Partner
from app.models.partner_contact import PartnerContact
from app.models.partner_collaboration import PartnerCollaboration
from app.models.target_list import TargetList
from app.models.target_list_item import TargetListItem
from app.models.speaker import Speaker
from app.models.speaker_contact import SpeakerContact
from app.models.task import Task
from app.models.goal import Goal
from app.models.mkt_timeline import MktTimelineItem
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.models.import_batch import ImportBatch, ImportRow
from app.models.invite import Invite

__all__ = [
    "User",
    "Department",
    "Project",
    "Partner",
    "PartnerContact",
    "PartnerCollaboration",
    "TargetList",
    "TargetListItem",
    "Speaker",
    "SpeakerContact",
    "Task",
    "Goal",
    "MktTimelineItem",
    "Notification",
    "ActivityLog",
    "ImportBatch",
    "ImportRow",
    "Invite",
]