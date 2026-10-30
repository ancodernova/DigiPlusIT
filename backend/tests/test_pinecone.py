from types import SimpleNamespace

from app.services import pinecone_service


def test_namespace_and_ids_are_tenant_scoped():
    assert pinecone_service.namespace("workspace-a").endswith(":workspace-a")
    assert pinecone_service.deterministic_id("workspace-a", "source", "0") != pinecone_service.deterministic_id("workspace-b", "source", "0")


def test_chunking_preserves_paragraph_boundaries():
    chunks = pinecone_service.chunk_text("First paragraph.\n\nSecond paragraph.", chunk_size=30, overlap=5)
    assert len(chunks) == 2
    assert chunks[0] == "First paragraph."
    assert chunks[1].endswith("Second paragraph.")


def test_document_index_upsert_and_search(monkeypatch):
    stored = []

    class Documents:
        def upsert(self, *, documents, namespace):
            stored.extend(documents)

        def search(self, **kwargs):
            return SimpleNamespace(matches=[SimpleNamespace(to_dict=lambda: {"_id": stored[0]["_id"], "_score": 0.9, "chunk_text": stored[0]["chunk_text"], "source_id": stored[0]["source_id"]})])

    fake_index = SimpleNamespace(documents=Documents())
    monkeypatch.setattr(pinecone_service, "_index", lambda: fake_index)
    monkeypatch.setattr(pinecone_service, "embed_texts", lambda texts: [[0.0, 1.0] for _ in texts])
    result = pinecone_service.upsert_vectors("workspace-a", [{"source_id": "doc-1", "chunk_id": "0", "text": "Useful evidence", "source_type": "knowledge"}])
    assert result["count"] == 1
    assert stored[0]["_id"] == pinecone_service.deterministic_id("workspace-a", "doc-1", "0")
    assert pinecone_service.search_text("workspace-a", "evidence")[0]["source_id"] == "doc-1"


def test_empty_upsert_is_idempotent():
    assert pinecone_service.upsert_vectors("workspace-a", []) == {"indexed": True, "count": 0}
