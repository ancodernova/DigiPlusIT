"""Live meeting capture routes."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_workspace
from app.schemas.transcript import LiveSessionCreate
from app.services import live_session_service

router = APIRouter(prefix="/meetings", tags=["Live Sessions"])


@router.post("/{meeting_id}/live-sessions", status_code=201)
def create_live_session(meeting_id: str, data: LiveSessionCreate, context=Depends(get_current_workspace)):
    return live_session_service.create_session(meeting_id, data, context)


@router.get("/{meeting_id}/live-sessions")
def list_live_sessions(meeting_id: str, context=Depends(get_current_workspace)):
    return live_session_service.list_sessions(meeting_id, context)


@router.get("/{meeting_id}/live-sessions/{session_id}")
def get_live_session(meeting_id: str, session_id: str, context=Depends(get_current_workspace)):
    return live_session_service.get_session(meeting_id, session_id, context)


@router.post("/{meeting_id}/live-sessions/{session_id}/stop")
def stop_live_session(meeting_id: str, session_id: str, context=Depends(get_current_workspace)):
    return live_session_service.stop_session(meeting_id, session_id, context)
