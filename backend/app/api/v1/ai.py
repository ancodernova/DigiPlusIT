"""Groq-backed AI routes."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.core.dependencies import get_current_workspace
from app.core.serialization import serialize_document
from app.database import get_database
from app.schemas.ai import MeetingAnalysisRequest, MeetingApproval, WorkspaceQuestion
from app.schemas.task import TaskCreate
from app.services import meeting_service, task_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI"])


def _ask_groq(prompt: str) -> dict:
    if not settings.GROQ_API_KEY:
        raise HTTPException(503, "AI provider is not configured")
    try:
        from groq import Groq
        response = Groq(api_key=settings.GROQ_API_KEY).chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "system", "content": "Return valid JSON only. Do not invent facts."}, {"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
        return json.loads(response.choices[0].message.content)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("AI request failed", extra={"model": settings.GROQ_MODEL})
        raise HTTPException(503, "AI provider is temporarily unavailable") from exc


@router.post("/meetings/analyze")
def analyze_meeting(data: MeetingAnalysisRequest, context=Depends(get_current_workspace)):
    db, notes = get_database(), data.raw_notes
    meeting = None
    if data.meeting_id:
        from app.core.dependencies import object_id
        meeting = db.meetings.find_one({"_id": object_id(data.meeting_id, "meeting ID"), "workspace_id": context["workspace"]["_id"]})
        if not meeting: raise HTTPException(404, "Meeting not found")
        notes = meeting.get("raw_notes") or ""
    if not notes: raise HTTPException(400, "meeting_id or raw_notes is required")
    return _ask_groq("Analyze these meeting notes. Return keys executive_summary, discussion_points, decisions, action_items, risks, blockers, follow_up_recommendations. Unknown owners and dates must be null.\n" + notes)


@router.post("/workspace/ask")
def ask_workspace(data: WorkspaceQuestion, context=Depends(get_current_workspace)):
    db, workspace_id = get_database(), context["workspace"]["_id"]
    records = list(db.meetings.find({"workspace_id": workspace_id}).sort("meeting_date", -1).limit(10))
    records += list(db.tasks.find({"workspace_id": workspace_id}).sort("updated_at", -1).limit(20))
    records += list(db.knowledge_documents.find({"workspace_id": workspace_id}).limit(20))
    compact = [{"type": item.get("document_type", "meeting" if "meeting_date" in item else "task"), "id": str(item["_id"]), "title": item.get("title", "")} for item in records]
    answer = _ask_groq(f"Answer only from this workspace context. If unavailable, say so. Question: {data.question}\nContext: {json.dumps(serialize_document(records), default=str)}")
    answer["sources"] = compact
    return answer


@router.post("/meetings/{meeting_id}/approve")
def approve_meeting(meeting_id: str, data: MeetingApproval, context=Depends(get_current_workspace)):
    if data.meeting_id != meeting_id:
        raise HTTPException(400, "Meeting ID does not match request path")
    meeting_service.get_meeting(meeting_id, context)
    created_tasks = [task_service.create_task(TaskCreate(**item.model_dump(), source_meeting_id=meeting_id), context) for item in data.tasks]
    created_decisions = [meeting_service.add_decision(meeting_id, item, context) for item in data.decisions]
    return {"tasks": created_tasks, "decisions": created_decisions}
