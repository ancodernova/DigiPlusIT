"""Meeting, decision, and participant schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    meeting_type: Literal["team_meeting", "project_review", "client_meeting", "work_handover", "sprint_planning", "other"] = "other"
    team_id: str | None = None
    agenda: str | None = None
    raw_notes: str | None = None
    meeting_date: datetime
    participants: list[str] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    agenda: str | None = None
    raw_notes: str | None = None
    status: Literal["scheduled", "in_progress", "completed", "cancelled"] | None = None
    meeting_date: datetime | None = None


class ParticipantAdd(BaseModel):
    user_id: str


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class MeetingTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_id: str | None = None
    due_date: datetime | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
