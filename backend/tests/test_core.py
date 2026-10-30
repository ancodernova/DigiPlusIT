from datetime import datetime, timezone

from bson import ObjectId

from app.core.serialization import serialize_document
from app.services.context_passport_service import markdown
from app.api.v1.ai import _ask_groq
from fastapi import HTTPException


def test_serialization_converts_mongodb_values():
    identifier = ObjectId()
    value = serialize_document({"_id": identifier, "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc), "items": [identifier]})
    assert value["_id"] == str(identifier)
    assert value["items"] == [str(identifier)]
    assert value["created_at"].startswith("2026-01-01")


def test_context_passport_markdown_contains_sources():
    result = markdown({
        "title": "Release handover",
        "content": {
            "objective": "Ship release",
            "current_status": "active",
            "important_decisions": [{"title": "Use staged rollout"}],
            "open_tasks": [{"title": "Finish runbook"}],
            "risks_and_blockers": [],
            "recommended_next_steps": [{"title": "Schedule review"}],
        },
    })
    assert "# Release handover" in result
    assert "Finish runbook" in result
    assert "Schedule review" in result


def test_ai_provider_failure_is_explicit(monkeypatch):
    monkeypatch.setattr("app.api.v1.ai.settings.GROQ_API_KEY", "")
    try:
        _ask_groq("test")
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("Expected an explicit 503 when Groq is unavailable")
