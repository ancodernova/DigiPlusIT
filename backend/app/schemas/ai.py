"""AI request and response schemas."""

from pydantic import BaseModel, Field


class MeetingAnalysisRequest(BaseModel):
    meeting_id: str | None = None
    raw_notes: str | None = Field(default=None, min_length=1)


class WorkspaceQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class ApprovedTask(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    owner_id: str | None = None
    due_date: str | None = None
    priority: str = "medium"


class ApprovedDecision(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class MeetingApproval(BaseModel):
    meeting_id: str
    tasks: list[ApprovedTask] = Field(default_factory=list)
    decisions: list[ApprovedDecision] = Field(default_factory=list)
