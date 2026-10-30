"""Task API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])
