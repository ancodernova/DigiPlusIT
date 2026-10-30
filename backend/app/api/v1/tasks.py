"""Task API routes."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_workspace
from app.schemas.task import CarryForwardRequest, TaskCreate, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/")
def list_tasks(context=Depends(get_current_workspace), task_status: str | None = Query(default=None, alias="status"), owner_id: str | None = None, team_id: str | None = None, priority: str | None = None, overdue: bool = False, search: str | None = None):
    return task_service.list_tasks(context, task_status, owner_id, team_id, priority, overdue, search)


@router.post("/", status_code=201)
def create_task(data: TaskCreate, context=Depends(get_current_workspace)):
    return task_service.create_task(data, context)


@router.get("/{task_id}")
def get_task(task_id: str, context=Depends(get_current_workspace)):
    return task_service.get_task(task_id, context)


@router.patch("/{task_id}")
def update_task(task_id: str, data: TaskUpdate, context=Depends(get_current_workspace)):
    return task_service.update_task(task_id, data, context)


@router.get("/{task_id}/history")
def history(task_id: str, context=Depends(get_current_workspace)):
    return task_service.task_history(task_id, context)


@router.post("/{task_id}/carry-forward")
def carry_forward(task_id: str, data: CarryForwardRequest, context=Depends(get_current_workspace)):
    return task_service.carry_forward(task_id, data.meeting_id, context)


@router.get("/meeting/{meeting_id}/open")
def meeting_open_tasks(meeting_id: str, context=Depends(get_current_workspace)):
    return task_service.open_meeting_tasks(meeting_id, context)
