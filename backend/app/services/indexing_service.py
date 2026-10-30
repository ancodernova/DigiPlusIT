"""Idempotent MongoDB-to-Pinecone indexing helpers."""

import logging
from datetime import datetime, timezone

from app.core.serialization import serialize_document
from app.database import get_database
from app.services.pinecone_service import index_text, update_vectors, delete_source_vectors

logger = logging.getLogger(__name__)


def index_record(collection: str, record: dict, text: str, source_type: str) -> dict:
    source_id = str(record["_id"])
    workspace_id = str(record["workspace_id"])
    metadata = {
        "workspace_id": workspace_id,
        "source_id": source_id,
        "source_type": source_type,
        "title": record.get("title"),
        "meeting_id": str(record["meeting_id"]) if record.get("meeting_id") else None,
        "transcript_id": str(record["transcript_id"]) if record.get("transcript_id") else None,
        "document_id": source_id if collection == "knowledge_documents" else None,
        "task_id": source_id if collection == "tasks" else None,
        "timestamp": str(record.get("created_at")) if record.get("created_at") else None,
    }
    db = get_database()
    now = datetime.now(timezone.utc)
    db.indexing_jobs.update_one(
        {"workspace_id": workspace_id, "source_id": source_id},
        {"$set": {"collection": collection, "source_type": source_type, "status": "processing",
                  "updated_at": now, "error": None},
         "$setOnInsert": {"created_at": now, "attempts": 0}},
        upsert=True,
    )
    db[collection].update_one({"_id": record["_id"]}, {"$set": {"indexing_status": "processing", "indexing_error": None}})
    try:
        result = index_text(workspace_id, source_id, text, metadata)
    except Exception as error:
        mark_indexing_failed(collection, record, error)
        raise
    db.indexing_jobs.update_one(
        {"workspace_id": workspace_id, "source_id": source_id},
        {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc), "completed_at": datetime.now(timezone.utc)},
         "$inc": {"attempts": 1}},
    )
    db[collection].update_one({"_id": record["_id"]}, {"$set": {"indexing_status": "completed", "indexing_error": None}})
    return result


def mark_indexing_failed(collection: str, record: dict, error: Exception) -> None:
    db = get_database()
    workspace_id = str(record["workspace_id"])
    source_id = str(record["_id"])
    db[collection].update_one({"_id": record["_id"]}, {"$set": {"indexing_status": "failed", "indexing_error": "Vector indexing failed"}})
    db.indexing_jobs.update_one(
        {"workspace_id": workspace_id, "source_id": source_id},
        {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc), "error": "Vector indexing failed"},
         "$inc": {"attempts": 1}},
    )
    logger.error("Vector indexing failed", extra={"collection": collection, "record_id": str(record_id), "error_type": type(error).__name__})


def remove_record(collection: str, record: dict) -> None:
    delete_source_vectors(str(record["workspace_id"]), str(record["_id"]))
