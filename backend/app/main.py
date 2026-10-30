"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from .config import get_settings
from .init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize application resources during startup."""

    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, Any]:
    """Return the service health status."""

    return {"status": "ok", "service": settings.app_name}
