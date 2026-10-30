"""Meeting API routes."""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_workspace
from app.schemas.meeting import DecisionCreate, MeetingCreate, MeetingTaskCreate, MeetingUpdate, ParticipantAdd
from app.schemas.task import TaskCreate
from app.services import task_service
from app.services import meeting_service

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.get("/")
def list_meetings(context=Depends(get_current_workspace), skip: int = 0, limit: int = 50, search: str | None = None, meeting_status: str | None = Query(default=None, alias="status")):
    return meeting_service.list_meetings(context, skip, limit, search, meeting_status)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_meeting(data: MeetingCreate, context=Depends(get_current_workspace)):
    return meeting_service.create_meeting(data, context)


@router.get("/{meeting_id}")
def get_meeting(meeting_id: str, context=Depends(get_current_workspace)):
    return meeting_service.get_meeting(meeting_id, context)


@router.patch("/{meeting_id}")
def update_meeting(meeting_id: str, data: MeetingUpdate, context=Depends(get_current_workspace)):
    return meeting_service.update_meeting(meeting_id, data, context)


@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: str, context=Depends(get_current_workspace)):
    return meeting_service.delete_meeting(meeting_id, context)


@router.post("/{meeting_id}/participants")
def add_participant(meeting_id: str, data: ParticipantAdd, context=Depends(get_current_workspace)):
    return meeting_service.add_participant(meeting_id, data.user_id, context)


@router.get("/{meeting_id}/participants")
def participants(meeting_id: str, context=Depends(get_current_workspace)):
    return meeting_service.get_meeting(meeting_id, context).get("participants", [])


@router.post("/{meeting_id}/decisions", status_code=201)
def add_decision(meeting_id: str, data: DecisionCreate, context=Depends(get_current_workspace)):
    return meeting_service.add_decision(meeting_id, data, context)


@router.get("/{meeting_id}/decisions")
def decisions(meeting_id: str, context=Depends(get_current_workspace)):
    return meeting_service.list_decisions(meeting_id, context)


@router.post("/{meeting_id}/tasks", status_code=201)
def create_meeting_task(meeting_id: str, data: MeetingTaskCreate, context=Depends(get_current_workspace)):
    meeting_service.get_meeting(meeting_id, context)
    return task_service.create_task(TaskCreate(**data.model_dump(), source_meeting_id=meeting_id), context)
