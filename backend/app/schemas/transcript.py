"""Transcript ingestion and live-session schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TranscriptPasteRequest(BaseModel):
    meeting_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    transcript_text: str = Field(min_length=1, max_length=5_000_000)
    meeting_date: datetime | None = None
    participants: list[str] = Field(default_factory=list)
    source: Literal["manual_paste"] = "manual_paste"
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=200)


class LiveSessionCreate(BaseModel):
    meeting_url: str = Field(min_length=8, max_length=2000)
    provider: Literal["mock", "zoom", "google_meet", "microsoft_teams"] = "mock"
    consent_confirmed: bool


class TranscriptAnalyzeRequest(BaseModel):
    force: bool = False
