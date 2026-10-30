"""Context Passport generation from persisted workspace records."""

from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.dependencies import object_id
from app.core.serialization import serialize_document
from app.database import get_database
from app.services.indexing_service import index_record, mark_indexing_failed


def generate_passport(data, context):
    db, workspace_id, now = get_database(), context["workspace"]["_id"], datetime.now(timezone.utc)
    meetings_query = {"workspace_id": workspace_id}
    if data.meeting_ids:
        meetings_query["_id"] = {"$in": [object_id(item, "meeting ID") for item in data.meeting_ids]}
    meetings = list(db.meetings.find(meetings_query).sort("meeting_date", -1).limit(50))
    tasks = list(db.tasks.find({"workspace_id": workspace_id}).sort("updated_at", -1).limit(200))
    decisions = list(db.decisions.find({"workspace_id": workspace_id}).sort("created_at", -1).limit(100))
    content = {
        "objective": None,
        "current_status": "active",
        "important_decisions": serialize_document(decisions),
        "open_tasks": serialize_document([x for x in tasks if x.get("status") != "completed"]),
        "completed_tasks": serialize_document([x for x in tasks if x.get("status") == "completed"]),
        "risks_and_blockers": serialize_document([x for x in tasks if x.get("status") == "blocked"]),
        "upcoming_deadlines": serialize_document([x for x in tasks if x.get("status") != "completed" and x.get("due_date")]),
        "key_stakeholders": serialize_document([x for x in db.workspace_members.find({"workspace_id": workspace_id, "is_active": True})]),
        "recommended_next_steps": serialize_document([x for x in tasks if x.get("status") in ("open", "blocked")][:10]),
        "source_meetings": serialize_document(meetings),
        "relevant_knowledge_documents": serialize_document(list(db.knowledge_documents.find({"workspace_id": workspace_id}).limit(50))),
    }
    doc = {"workspace_id": workspace_id, "title": data.title, "content": content, "source_meeting_ids": [x["_id"] for x in meetings], "source_task_ids": [x["_id"] for x in tasks], "generated_by": context["user"]["_id"], "created_at": now}
    result = db.context_passports.insert_one(doc)
    saved = db.context_passports.find_one({"_id": result.inserted_id})
    try:
        index_record("context_passports", saved, str(content), "context_passport")
    except Exception as exc:
        mark_indexing_failed("context_passports", saved["_id"], exc)
    return serialize_document(db.context_passports.find_one({"_id": result.inserted_id}))


def list_passports(context):
    return [serialize_document(x) for x in get_database().context_passports.find({"workspace_id": context["workspace"]["_id"]}).sort("created_at", -1)]


def get_passport(passport_id, context):
    item = get_database().context_passports.find_one({"_id": object_id(passport_id, "passport ID"), "workspace_id": context["workspace"]["_id"]})
    if not item:
        raise HTTPException(404, "Context Passport not found")
    return serialize_document(item)


def markdown(passport):
    content = passport["content"]
    lines = [f"# {passport['title']}", "", f"## Objective\n{content.get('objective') or 'Not specified'}", f"## Current status\n{content.get('current_status')}"]
    for key, heading in (("important_decisions", "Important decisions"), ("open_tasks", "Open tasks"), ("risks_and_blockers", "Risks and blockers"), ("recommended_next_steps", "Recommended next steps")):
        lines.append(f"## {heading}")
        for item in content.get(key, []):
            lines.append(f"- {item.get('title', item.get('description', str(item)))}")
    return "\n".join(lines)
