
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import (
    connect_to_mongodb,
    close_mongodb_connection,
    get_database
)
from app.init_db import initialize_database
from app.core.logging import configure_logging
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    connect_to_mongodb()
    initialize_database()

    yield

    close_mongodb_connection()


# 1. Create the FastAPI application FIRST
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered organizational knowledge continuity platform",
    version="1.0.0",
    lifespan=lifespan
)


# 2. Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# 3. Register API routes AFTER app creation
app.include_router(api_router)


# 4. Basic endpoints
@app.get("/")
def root():
    return {
        "application": "ContextFlow AI",
        "status": "running"
    }


@app.get("/health")
def health():
    get_database().command("ping")

    return {
        "status": "healthy",
        "database": "connected"
    }
