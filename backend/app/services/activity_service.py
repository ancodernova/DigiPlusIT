"""Workspace activity and audit logging."""

from datetime import datetime, timezone

from app.database import get_database


def record_activity(context, event_type, entity_type, entity_id, metadata=None, request_id=None):
    get_database().activity_logs.insert_one({
        "workspace_id": context["workspace"]["_id"],
        "user_id": context["user"]["_id"],
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "request_id": request_id,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc),
    })
