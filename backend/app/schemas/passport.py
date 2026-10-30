"""Context Passport schemas."""

from pydantic import BaseModel, Field


class PassportGenerateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    meeting_ids: list[str] = Field(default_factory=list)
    team_id: str | None = None
