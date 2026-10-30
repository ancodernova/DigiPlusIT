"""Tenant-isolated Pinecone vector service."""

from hashlib import sha256

from fastapi import HTTPException

from app.config import settings
DOCUMENT_TITLE_FIELD = "title"
DOCUMENT_TEXT_FIELD = "chunk_text"
DOCUMENT_METADATA_FIELDS = (
    "workspace_id",
    "meeting_id",
    "transcript_id",
    "document_id",
    "task_id",
    "source_type",
    "source_id",
    "chunk_id",
    "timestamp",
    "speaker",
    "text_reference",
)


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
    details = description.to_dict() if hasattr(description, "to_dict") else {}
    embed = details.get("embed", {})
    schema = details.get("schema", {}).get("fields", {})
    return {
        "connected": True,
        "exists": True,
        "index": settings.PINECONE_INDEX_NAME,
        "dimension": getattr(description, "dimension", None) or embed.get("dimension") or schema.get(DOCUMENT_TEXT_FIELD, {}).get("read_parameters", {}).get("dimension"),
        "metric": getattr(description, "metric", None) or embed.get("metric"),
        "host": bool(getattr(description, "host", None)),
        "schema_fields": sorted(schema),
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
    payload = []
    for record in records:
        metadata = {
            key: value
            for key, value in record.items()
            if key in DOCUMENT_METADATA_FIELDS and key not in {"text", "title"} and value is not None
        }
        metadata["text_reference"] = record["text"][:500]
        payload.append({
            "_id": record.get("id") or deterministic_id(
                workspace_id, str(record.get("source_id", "")), str(record.get("chunk_id", "0"))
            ),
            DOCUMENT_TITLE_FIELD: record.get("title") or record.get("source_type", "ContextFlow"),
            DOCUMENT_TEXT_FIELD: record["text"],
            **metadata,
        })
    _index().upsert_records(records=payload, namespace=namespace(workspace_id))
    return {"indexed": True, "count": len(payload), "ids": [item["_id"] for item in payload]}


def index_text(workspace_id: str, source_id: str, text: str, metadata: dict) -> dict:
    records = []
    for number, chunk in enumerate(chunk_text(text)):
        records.append({"source_id": source_id, "chunk_id": str(number), "text": chunk, **metadata})
    return upsert_vectors(workspace_id, records)


def search_vectors(workspace_id: str, vector: list[float], top_k: int = 5) -> list[dict]:
    raise HTTPException(501, "The configured Pinecone document index requires text search")


def search_text(workspace_id: str, query: str, top_k: int = 5) -> list[dict]:
    result = _index().search_records(
        namespace=namespace(workspace_id),
        top_k=min(max(top_k, 1), 50),
        inputs={"text": query},
        fields=[DOCUMENT_TITLE_FIELD, DOCUMENT_TEXT_FIELD, *DOCUMENT_METADATA_FIELDS],
    )
    result_data = result.to_dict() if hasattr(result, "to_dict") else result
    hits = result_data.get("result", {}).get("hits", []) if isinstance(result_data, dict) else []
    return [
        {"_id": hit.get("_id") or hit.get("id"), "_score": hit.get("_score", hit.get("score")), **hit.get("fields", {})}
        for hit in hits
    ]


def delete_vectors(workspace_id: str, ids: list[str]) -> None:
    if ids:
        _index().delete(ids=ids, namespace=namespace(workspace_id))


def update_vectors(workspace_id: str, source_id: str, text: str, metadata: dict) -> dict:
    delete_source_vectors(workspace_id, source_id)
    return index_text(workspace_id, source_id, text, metadata)


def delete_source_vectors(workspace_id: str, source_id: str) -> None:
    _index().delete(filter={"source_id": source_id}, namespace=namespace(workspace_id))
