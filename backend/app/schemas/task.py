"""Task schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    source_meeting_id: str | None = None
    team_id: str | None = None
    owner_id: str | None = None
    due_date: datetime | None = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    owner_id: str | None = None
    due_date: datetime | None = None
    priority: Literal["low", "medium", "high", "critical"] | None = None
    status: Literal["open", "in_progress", "blocked", "completed"] | None = None
    outcome: str | None = None


class CarryForwardRequest(BaseModel):
    meeting_id: str


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    document_type: str = "note"
