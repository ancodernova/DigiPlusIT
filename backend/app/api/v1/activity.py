"""Activity and notification routes."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_workspace
from app.core.serialization import serialize_document
from app.database import get_database

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/")
def list_activity(context=Depends(get_current_workspace), limit: int = 50):
    items = get_database().activity_logs.find({"workspace_id": context["workspace"]["_id"]}).sort("created_at", -1).limit(min(limit, 100))
    return [serialize_document(item) for item in items]


@router.get("/notifications")
def notifications(context=Depends(get_current_workspace), limit: int = 50):
    items = get_database().notifications.find({"user_id": context["user"]["_id"]}).sort("created_at", -1).limit(min(limit, 100))
    return [serialize_document(item) for item in items]
