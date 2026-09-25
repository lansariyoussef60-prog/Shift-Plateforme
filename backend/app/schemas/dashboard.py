from typing import Dict

from pydantic import BaseModel

from app.schemas.task import TaskCounts


class MyDashboardOut(BaseModel):
    task_counts: TaskCounts


class TeamDashboardOut(BaseModel):
    team_size: int
    task_counts: TaskCounts


class PartnerPipelineCounts(BaseModel):
    new: int
    contacted: int
    follow_up: int
    negotiation: int
    signed: int
    rejected: int
    not_interested: int


class SpeakerPipelineCounts(BaseModel):
    prospect: int
    contacted: int
    interested: int
    confirmed: int
    declined: int
    follow_up: int


class ProjectDashboardOut(BaseModel):
    total_users: int
    users_by_role: Dict[str, int]
    task_counts: TaskCounts
    partner_pipeline: PartnerPipelineCounts
    speaker_pipeline: SpeakerPipelineCounts
