"""Workspace knowledge document routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_workspace, object_id
from app.core.serialization import serialize_document
from app.database import get_database
from app.schemas.task import KnowledgeDocumentCreate
from app.schemas.knowledge import KnowledgeDocumentUpdate, KnowledgeLinkRequest

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post("/", status_code=201)
def create_document(data: KnowledgeDocumentCreate, context=Depends(get_current_workspace)):
    now = datetime.now(timezone.utc)
    document = {**data.model_dump(), "workspace_id": context["workspace"]["_id"], "uploaded_by": context["user"]["_id"], "created_at": now, "updated_at": now}
    result = get_database().knowledge_documents.insert_one(document)
    return serialize_document(get_database().knowledge_documents.find_one({"_id": result.inserted_id}))


@router.get("/")
def list_documents(context=Depends(get_current_workspace), search: str | None = Query(default=None)):
    query = {"workspace_id": context["workspace"]["_id"]}
    if search:
        query["$text"] = {"$search": search}
    return [serialize_document(x) for x in get_database().knowledge_documents.find(query).sort("created_at", -1)]


@router.get("/{document_id}")
def get_document(document_id: str, context=Depends(get_current_workspace)):
    item = get_database().knowledge_documents.find_one({"_id": object_id(document_id, "document ID"), "workspace_id": context["workspace"]["_id"]})
    if not item: raise HTTPException(404, "Knowledge document not found")
    return serialize_document(item)


@router.delete("/{document_id}")
def delete_document(document_id: str, context=Depends(get_current_workspace)):
    result = get_database().knowledge_documents.delete_one({"_id": object_id(document_id, "document ID"), "workspace_id": context["workspace"]["_id"]})
    if not result.deleted_count: raise HTTPException(404, "Knowledge document not found")
    return {"deleted": True}


@router.patch("/{document_id}")
def update_document(document_id: str, data: KnowledgeDocumentUpdate, context=Depends(get_current_workspace)):
    db = get_database()
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    for key in ("source_meeting_id",):
        if updates.get(key):
            updates[key] = object_id(updates[key], "meeting ID")
    if updates.get("linked_task_ids") is not None:
        updates["linked_task_ids"] = [object_id(x, "task ID") for x in updates["linked_task_ids"]]
    updates["updated_at"] = datetime.now(timezone.utc)
    result = db.knowledge_documents.update_one({"_id": object_id(document_id, "document ID"), "workspace_id": context["workspace"]["_id"]}, {"$set": updates})
    if not result.matched_count:
        raise HTTPException(404, "Knowledge document not found")
    return get_document(document_id, context)


@router.post("/{document_id}/links")
def link_document(document_id: str, data: KnowledgeLinkRequest, context=Depends(get_current_workspace)):
    db = get_database()
    document = db.knowledge_documents.find_one({"_id": object_id(document_id, "document ID"), "workspace_id": context["workspace"]["_id"]})
    if not document:
        raise HTTPException(404, "Knowledge document not found")
    if data.meeting_id:
        meeting = db.meetings.find_one({"_id": object_id(data.meeting_id, "meeting ID"), "workspace_id": context["workspace"]["_id"]})
        if not meeting: raise HTTPException(404, "Meeting not found")
        db.knowledge_documents.update_one({"_id": document["_id"]}, {"$set": {"source_meeting_id": meeting["_id"]}})
    if data.task_id:
        task = db.tasks.find_one({"_id": object_id(data.task_id, "task ID"), "workspace_id": context["workspace"]["_id"]})
        if not task: raise HTTPException(404, "Task not found")
        db.knowledge_documents.update_one({"_id": document["_id"]}, {"$addToSet": {"linked_task_ids": task["_id"]}})
    return get_document(document_id, context)
