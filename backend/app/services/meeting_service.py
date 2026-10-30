"""Meeting and decision services."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException

from app.core.dependencies import object_id
from app.core.serialization import serialize_document
from app.database import get_database
from app.services.activity_service import record_activity
from app.services.indexing_service import index_record, mark_indexing_failed


def _meeting(db, meeting_id: str, workspace_id: ObjectId) -> dict:
    meeting = db.meetings.find_one({"_id": object_id(meeting_id, "meeting ID"), "workspace_id": workspace_id})
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


def create_meeting(data, context):
    db, now = get_database(), datetime.now(timezone.utc)
    document = data.model_dump()
    document.update({"workspace_id": context["workspace"]["_id"], "created_by": context["user"]["_id"], "status": "scheduled", "created_at": now, "updated_at": now})
    document["team_id"] = object_id(document["team_id"], "team ID") if document.get("team_id") else None
    document["participants"] = [object_id(item, "participant ID") for item in document["participants"]]
    result = db.meetings.insert_one(document)
    record_activity(context, "meeting_created", "meeting", result.inserted_id)
    return serialize_document(db.meetings.find_one({"_id": result.inserted_id}))


def list_meetings(context, skip=0, limit=50, search=None, status=None):
    query = {"workspace_id": context["workspace"]["_id"]}
    if status:
        query["status"] = status
    if search:
        query["$text"] = {"$search": search}
    return [serialize_document(item) for item in get_database().meetings.find(query).sort("meeting_date", -1).skip(skip).limit(min(limit, 100))]


def get_meeting(meeting_id, context):
    return serialize_document(_meeting(get_database(), meeting_id, context["workspace"]["_id"]))


def update_meeting(meeting_id, data, context):
    db = get_database()
    _meeting(db, meeting_id, context["workspace"]["_id"])
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    db.meetings.update_one({"_id": object_id(meeting_id), "workspace_id": context["workspace"]["_id"]}, {"$set": updates})
    record_activity(context, "meeting_updated", "meeting", object_id(meeting_id))
    return get_meeting(meeting_id, context)


def delete_meeting(meeting_id, context):
    db = get_database()
    _meeting(db, meeting_id, context["workspace"]["_id"])
    db.meetings.delete_one({"_id": object_id(meeting_id), "workspace_id": context["workspace"]["_id"]})
    record_activity(context, "meeting_deleted", "meeting", object_id(meeting_id))
    return {"deleted": True}


def add_participant(meeting_id, user_id, context):
    db = get_database()
    _meeting(db, meeting_id, context["workspace"]["_id"])
    participant = object_id(user_id, "user ID")
    if not db.workspace_members.find_one({"workspace_id": context["workspace"]["_id"], "user_id": participant, "is_active": True}):
        raise HTTPException(404, "User is not an active workspace member")
    db.meetings.update_one({"_id": object_id(meeting_id)}, {"$addToSet": {"participants": participant}})
    return get_meeting(meeting_id, context)


def add_decision(meeting_id, data, context):
    db, now = get_database(), datetime.now(timezone.utc)
    _meeting(db, meeting_id, context["workspace"]["_id"])
    decision = {"workspace_id": context["workspace"]["_id"], "meeting_id": object_id(meeting_id), "title": data.title, "description": data.description, "created_by": context["user"]["_id"], "created_at": now}
    result = db.decisions.insert_one(decision)
    saved = db.decisions.find_one({"_id": result.inserted_id})
    try:
        index_record("decisions", saved, f"{saved['title']}\n{saved['description']}", "decision")
    except Exception as exc:
        mark_indexing_failed("decisions", saved["_id"], exc)
    return serialize_document(db.decisions.find_one({"_id": result.inserted_id}))


def list_decisions(meeting_id, context):
    _meeting(get_database(), meeting_id, context["workspace"]["_id"])
    return [serialize_document(item) for item in get_database().decisions.find({"workspace_id": context["workspace"]["_id"], "meeting_id": object_id(meeting_id)}).sort("created_at", -1)]
