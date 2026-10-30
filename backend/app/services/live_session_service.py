"""Provider-independent live meeting session lifecycle."""

from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException

from app.core.dependencies import object_id
from app.core.serialization import serialize_document
from app.database import get_database


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise HTTPException(400, "Invalid meeting URL")


def create_session(meeting_id, data, context):
    validate_url(data.meeting_url)
    if not data.consent_confirmed:
        raise HTTPException(400, "Recording consent must be confirmed")
    if data.provider != "mock":
        raise HTTPException(503, f"{data.provider} provider is pending official integration configuration")
    db, now = get_database(), datetime.now(timezone.utc)
    mid = object_id(meeting_id, "meeting ID")
    if not db.meetings.find_one({"_id": mid, "workspace_id": context["workspace"]["_id"]}):
        raise HTTPException(404, "Meeting not found")
    result = db.live_sessions.insert_one({"workspace_id": context["workspace"]["_id"], "meeting_id": mid, "provider": "mock", "provider_session_id": None, "meeting_url": data.meeting_url, "status": "waiting", "consent_status": "confirmed", "created_by": context["user"]["_id"], "created_at": now, "started_at": now})
    return serialize_document(db.live_sessions.find_one({"_id": result.inserted_id}))


def get_session(meeting_id, session_id, context):
    item = get_database().live_sessions.find_one({"_id": object_id(session_id, "session ID"), "meeting_id": object_id(meeting_id, "meeting ID"), "workspace_id": context["workspace"]["_id"]})
    if not item:
        raise HTTPException(404, "Live session not found")
    return serialize_document(item)


def list_sessions(meeting_id, context):
    meeting = object_id(meeting_id, "meeting ID")
    items = get_database().live_sessions.find({
        "meeting_id": meeting,
        "workspace_id": context["workspace"]["_id"],
    }).sort("created_at", -1)
    return [serialize_document(item) for item in items]


def stop_session(meeting_id, session_id, context):
    db = get_database()
    get_session(meeting_id, session_id, context)
    db.live_sessions.update_one({"_id": object_id(session_id), "workspace_id": context["workspace"]["_id"]}, {"$set": {"status": "stopped", "ended_at": datetime.now(timezone.utc)}})
    return get_session(meeting_id, session_id, context)
