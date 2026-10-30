"""Database-driven dashboard routes."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_workspace
from app.core.serialization import serialize_document
from app.database import get_database

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def overview(context=Depends(get_current_workspace)):
    db, workspace_id = get_database(), context["workspace"]["_id"]
    tasks = db.tasks
    counts = {status: tasks.count_documents({"workspace_id": workspace_id, "status": status}) for status in ("open", "in_progress", "blocked", "completed")}
    return {"total_meetings": db.meetings.count_documents({"workspace_id": workspace_id}), "total_tasks": sum(counts.values()), "open_tasks": counts["open"] + counts["in_progress"], "completed_tasks": counts["completed"], "blocked_tasks": counts["blocked"], "overdue_tasks": tasks.count_documents({"workspace_id": workspace_id, "due_date": {"$lt": datetime.now(timezone.utc)}, "status": {"$ne": "completed"}}), "upcoming_deadlines": serialize_document(list(tasks.find({"workspace_id": workspace_id, "due_date": {"$gte": datetime.now(timezone.utc), "$lte": datetime.now(timezone.utc) + timedelta(days=7)}, "status": {"$ne": "completed"}}).sort("due_date", 1).limit(10))), "recent_decisions": [serialize_document(x) for x in db.decisions.find({"workspace_id": workspace_id}).sort("created_at", -1).limit(10)], "recent_meetings": [serialize_document(x) for x in db.meetings.find({"workspace_id": workspace_id}).sort("meeting_date", -1).limit(10)], "recent_activity": [serialize_document(x) for x in db.activity_logs.find({"workspace_id": workspace_id}).sort("created_at", -1).limit(10)]}


@router.get("/risks")
def risks(context=Depends(get_current_workspace)):
    db, workspace_id, now = get_database(), context["workspace"]["_id"], datetime.now(timezone.utc)
    overdue = list(db.tasks.find({"workspace_id": workspace_id, "due_date": {"$lt": now}, "status": {"$ne": "completed"}}))
    soon = list(db.tasks.find({"workspace_id": workspace_id, "due_date": {"$gte": now, "$lte": now + timedelta(days=7)}, "status": {"$ne": "completed"}}))
    blocked = list(db.tasks.find({"workspace_id": workspace_id, "status": "blocked"}))
    unassigned = list(db.tasks.find({"workspace_id": workspace_id, "owner_id": None, "status": {"$ne": "completed"}}))
    repeated = list(db.tasks.find({"workspace_id": workspace_id, "carry_forward_count": {"$gte": 2}, "status": {"$ne": "completed"}}))
    return {"overdue": serialize_document(overdue), "due_soon": serialize_document(soon), "blocked": serialize_document(blocked), "unassigned": serialize_document(unassigned), "repeatedly_carried_forward": serialize_document(repeated)}
