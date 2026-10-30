"""Knowledge document schemas."""

from pydantic import BaseModel, Field


class KnowledgeDocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    document_type: str | None = None
    source_meeting_id: str | None = None
    linked_task_ids: list[str] | None = None


class KnowledgeLinkRequest(BaseModel):
    meeting_id: str | None = None
    task_id: str | None = None
