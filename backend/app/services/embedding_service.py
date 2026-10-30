"""Provider-independent embedding generation."""

from functools import lru_cache

from fastapi import HTTPException

from app.config import settings


def provider_name() -> str:
    configured = settings.EMBEDDING_PROVIDER.strip().lower()
    if configured in {"pinecone", "pinecone_inference"}:
        return "pinecone_inference"
    if configured in {"", "your_embedding_provider"} and settings.PINECONE_API_KEY:
        return "pinecone_inference"
    return configured


def model_name() -> str:
    configured = settings.EMBEDDING_MODEL.strip()
    if configured in {"", "your_embedding_model"}:
        return "llama-text-embed-v2"
    return configured


@lru_cache(maxsize=1)
def _client():
    if not settings.PINECONE_API_KEY:
        raise HTTPException(503, "Embedding provider is not configured")
    from pinecone import Pinecone
    return Pinecone(api_key=settings.PINECONE_API_KEY)


def embed_texts(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    if not texts:
        return []
    if provider_name() != "pinecone_inference":
        raise HTTPException(503, f"Unsupported embedding provider: {provider_name()}")
    try:
        response = _client().inference.embed(
            model=model_name(),
            inputs=texts,
            parameters={"input_type": input_type, "truncate": "END"},
        )
        vectors = []
        for item in response:
            values = item.values if hasattr(item, "values") else item["values"]
            vectors.append(list(values))
        expected = settings.EMBEDDING_DIMENSIONS
        if expected and any(len(vector) != expected for vector in vectors):
            raise HTTPException(503, "Embedding dimensions do not match configuration")
        return vectors
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Embedding provider is temporarily unavailable") from exc


def embed_query(text: str) -> list[float]:
    return embed_texts([text], input_type="query")[0]


def dimension() -> int:
    return len(embed_texts(["dimension probe"])[0])
