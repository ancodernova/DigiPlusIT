from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.ai import router as ai_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.context_passports import router as passports_router
from app.api.v1.activity import router as activity_router
from app.api.v1.transcripts import router as transcripts_router
from app.api.v1.live_sessions import router as live_sessions_router
from app.api.v1.pinecone import router as pinecone_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(meetings_router)
api_router.include_router(tasks_router)
api_router.include_router(knowledge_router)
api_router.include_router(ai_router)
api_router.include_router(dashboard_router)
api_router.include_router(passports_router)
api_router.include_router(activity_router)
api_router.include_router(transcripts_router)
api_router.include_router(live_sessions_router)
api_router.include_router(pinecone_router)