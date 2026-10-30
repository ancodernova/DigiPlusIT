"""Tenant-isolated Pinecone vector service."""

from datetime import datetime
from hashlib import sha256

from fastapi import HTTPException

from app.config import settings
from app.services.embedding_service import embed_texts


def configured() -> bool:
    return bool(settings.PINECONE_API_KEY and settings.PINECONE_INDEX_NAME)


def namespace(workspace_id: str) -> str:
    return f"{settings.PINECONE_NAMESPACE_PREFIX}:{workspace_id}"


def _client():
    if not configured():
        raise HTTPException(503, "Pinecone is not configured")
    from pinecone import Pinecone
    return Pinecone(api_key=settings.PINECONE_API_KEY)


def _index():
    return _client().Index(settings.PINECONE_INDEX_NAME)


def check_index_health() -> dict:
    client = _client()
    indexes = [item.name for item in client.list_indexes()]
    if settings.PINECONE_INDEX_NAME not in indexes:
        return {"connected": False, "exists": False, "index": settings.PINECONE_INDEX_NAME}
    description = client.describe_index(settings.PINECONE_INDEX_NAME)
    return {
        "connected": True,
        "exists": True,
        "index": settings.PINECONE_INDEX_NAME,
        "dimension": getattr(description, "dimension", None),
        "metric": getattr(description, "metric", None),
        "host": bool(getattr(description, "host", None)),
    }


def validate_index_dimension() -> dict:
    health = check_index_health()
    if not health["exists"]:
        return health
    from app.services.embedding_service import dimension
    actual = dimension()
    health["embedding_dimension"] = actual
    health["dimension_matches"] = actual == health["dimension"]
    if not health["dimension_matches"]:
        raise HTTPException(503, "Embedding and Pinecone index dimensions do not match")
    return health


def deterministic_id(workspace_id: str, source_id: str, chunk_id: str) -> str:
    return sha256(f"{workspace_id}:{source_id}:{chunk_id}".encode()).hexdigest()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs or [text.strip()]:
        if current and len(current) + len(paragraph) + 1 > chunk_size:
            chunks.append(current)
            current = current[-overlap:] + "\n" + paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def upsert_vectors(workspace_id: str, records: list[dict]) -> dict:
    if not records:
        return {"indexed": True, "count": 0}
    texts = [record["text"] for record in records]
    vectors = embed_texts(texts)
    payload = []
    for record, vector in zip(records, vectors):
        metadata = {key: value for key, value in record.items() if key != "text" and value is not None}
        metadata["text_reference"] = record["text"][:500]
        payload.append({"_id": record.get("id") or deterministic_id(workspace_id, str(record.get("source_id", "")), str(record.get("chunk_id", "0"))), "title": record.get("title") or record.get("source_type", "ContextFlow"), "chunk_text": record["text"], **metadata})
    _index().documents.upsert(documents=payload, namespace=namespace(workspace_id))
    return {"indexed": True, "count": len(payload), "ids": [item["_id"] for item in payload]}


def index_text(workspace_id: str, source_id: str, text: str, metadata: dict) -> dict:
    records = []
    for number, chunk in enumerate(chunk_text(text)):
        records.append({"source_id": source_id, "chunk_id": str(number), "text": chunk, **metadata})
    return upsert_vectors(workspace_id, records)


def search_vectors(workspace_id: str, vector: list[float], top_k: int = 5) -> list[dict]:
    raise HTTPException(501, "The configured Pinecone document index requires text search")


def search_text(workspace_id: str, query: str, top_k: int = 5) -> list[dict]:
    from pinecone.models.documents.score_by import EmbedQuery
    result = _index().documents.search(
        namespace=namespace(workspace_id),
        score_by=[EmbedQuery(query=query, field="chunk_text")],
        top_k=min(max(top_k, 1), 50),
        include_fields=["title", "chunk_text", "workspace_id", "meeting_id", "transcript_id", "document_id", "task_id", "source_type", "source_id", "chunk_id", "timestamp"],
    )
    matches = result.get("matches", []) if isinstance(result, dict) else getattr(result, "matches", [])
    return [match.to_dict() if hasattr(match, "to_dict") else match for match in matches]


def delete_vectors(workspace_id: str, ids: list[str]) -> None:
    if ids:
        _index().documents.delete(ids=ids, namespace=namespace(workspace_id))


def update_vectors(workspace_id: str, source_id: str, text: str, metadata: dict) -> dict:
    delete_source_vectors(workspace_id, source_id)
    return index_text(workspace_id, source_id, text, metadata)


def delete_source_vectors(workspace_id: str, source_id: str) -> None:
    _index().documents.delete(filter={"source_id": source_id}, namespace=namespace(workspace_id))
