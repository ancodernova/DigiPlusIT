"""Task, history, and carry-forward services."""

from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.dependencies import object_id
from app.core.serialization import serialize_document
from app.database import get_database
from app.services.activity_service import record_activity
from app.services.indexing_service import index_record, mark_indexing_failed


def _task(db, task_id, workspace_id):
    item = db.tasks.find_one({"_id": object_id(task_id, "task ID"), "workspace_id": workspace_id})
    if not item:
        raise HTTPException(404, "Task not found")
    return item


def _assert_task_access(task, context, write=False):
    if context["membership"].get("role") != "member":
        return
    if task.get("owner_id") != context["user"]["_id"]:
        raise HTTPException(403, "Members can access only their assigned tasks")
    if write:
        raise HTTPException(403, "Members may update only the status and outcome of assigned tasks")


def create_task(data, context):
    db, now = get_database(), datetime.now(timezone.utc)
    document = data.model_dump()
    document.update({"workspace_id": context["workspace"]["_id"], "created_by": context["user"]["_id"], "status": "open", "carry_forward_count": 0, "created_at": now, "updated_at": now})
    for key in ("source_meeting_id", "team_id", "owner_id"):
        if document.get(key):
            document[key] = object_id(document[key], key.replace("_", " "))
    result = db.tasks.insert_one(document)
    record_activity(context, "task_created", "task", result.inserted_id)
    db.task_history.insert_one({"task_id": result.inserted_id, "workspace_id": document["workspace_id"], "event": "task_created", "old_value": None, "new_value": document.copy(), "created_by": context["user"]["_id"], "created_at": now})
    saved = db.tasks.find_one({"_id": result.inserted_id})
    try:
        index_record("tasks", saved, f"{saved['title']}\n{saved.get('description') or ''}", "task")
    except Exception as exc:
        mark_indexing_failed("tasks", saved["_id"], exc)
    return serialize_document(db.tasks.find_one({"_id": result.inserted_id}))


def list_tasks(context, status=None, owner_id=None, team_id=None, priority=None, overdue=False, search=None):
    db, query = get_database(), {"workspace_id": context["workspace"]["_id"]}
    if context["membership"].get("role") == "member":
        query["owner_id"] = context["user"]["_id"]
    if status: query["status"] = status
    if owner_id: query["owner_id"] = object_id(owner_id, "owner ID")
    if team_id: query["team_id"] = object_id(team_id, "team ID")
    if priority: query["priority"] = priority
    if overdue: query["due_date"] = {"$lt": datetime.now(timezone.utc)}; query["status"] = {"$ne": "completed"}
    if search: query["$text"] = {"$search": search}
    return [serialize_document(item) for item in db.tasks.find(query).sort("due_date", 1)]


def get_task(task_id, context):
    task = _task(get_database(), task_id, context["workspace"]["_id"])
    _assert_task_access(task, context)
    return serialize_document(task)


def update_task(task_id, data, context):
    db, current = get_database(), _task(get_database(), task_id, context["workspace"]["_id"])
    if context["membership"].get("role") == "member":
        _assert_task_access(current, context)
        allowed = {"status", "outcome"}
        if any(key not in allowed for key in data.model_dump(exclude_unset=True)):
            raise HTTPException(403, "Members may update only task status and outcome")
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    for key in ("owner_id",):
        if updates.get(key): updates[key] = object_id(updates[key], "owner ID")
    if updates.get("status") == "completed": updates["completed_at"] = datetime.now(timezone.utc)
    updates["updated_at"] = datetime.now(timezone.utc)
    db.tasks.update_one({"_id": current["_id"]}, {"$set": updates})
    saved = db.tasks.find_one({"_id": current["_id"]})
    try:
        index_record("tasks", saved, f"{saved['title']}\n{saved.get('description') or ''}", "task")
    except Exception as exc:
        mark_indexing_failed("tasks", saved["_id"], exc)
    record_activity(context, "task_updated", "task", current["_id"], {"fields": list(updates)})
    for key, value in updates.items():
        if key not in ("updated_at", "completed_at") and current.get(key) != value:
            db.task_history.insert_one({"task_id": current["_id"], "workspace_id": current["workspace_id"], "event": f"{key}_changed", "old_value": serialize_document(current.get(key)), "new_value": serialize_document(value), "created_by": context["user"]["_id"], "created_at": updates["updated_at"]})
    return get_task(task_id, context)


def task_history(task_id, context):
    _assert_task_access(_task(get_database(), task_id, context["workspace"]["_id"]), context)
    return [serialize_document(item) for item in get_database().task_history.find({"task_id": object_id(task_id), "workspace_id": context["workspace"]["_id"]}).sort("created_at", -1)]


def carry_forward(task_id, meeting_id, context):
    db, now = get_database(), datetime.now(timezone.utc)
    task = _task(db, task_id, context["workspace"]["_id"])
    _assert_task_access(task, context)
    meeting = db.meetings.find_one({"_id": object_id(meeting_id, "meeting ID"), "workspace_id": context["workspace"]["_id"]})
    if not meeting: raise HTTPException(404, "Meeting not found")
    if task.get("status") == "completed": raise HTTPException(409, "Completed tasks cannot be carried forward")
    link = {"task_id": task["_id"], "meeting_id": meeting["_id"], "workspace_id": task["workspace_id"], "link_type": "carry_forward", "created_by": context["user"]["_id"], "created_at": now}
    try: db.task_meeting_links.insert_one(link)
    except Exception as exc:
        if "duplicate" in str(exc).lower(): raise HTTPException(409, "Task is already linked to this meeting")
        raise
    db.tasks.update_one({"_id": task["_id"]}, {"$inc": {"carry_forward_count": 1}, "$set": {"updated_at": now}})
    db.task_history.insert_one({"task_id": task["_id"], "workspace_id": task["workspace_id"], "event": "carried_forward", "old_value": task.get("carry_forward_count", 0), "new_value": task.get("carry_forward_count", 0) + 1, "meeting_id": meeting["_id"], "created_by": context["user"]["_id"], "created_at": now})
    record_activity(context, "task_carried_forward", "task", task["_id"], {"meeting_id": meeting["_id"]})
    return get_task(task_id, context)


def open_meeting_tasks(meeting_id, context):
    db = get_database()
    meeting = db.meetings.find_one({"_id": object_id(meeting_id, "meeting ID"), "workspace_id": context["workspace"]["_id"]})
    if not meeting: raise HTTPException(404, "Meeting not found")
    links = db.task_meeting_links.find({"meeting_id": meeting["_id"], "workspace_id": meeting["workspace_id"]})
    ids = [link["task_id"] for link in links]
    return [serialize_document(item) for item in db.tasks.find({"_id": {"$in": ids}, "status": {"$ne": "completed"}})]
