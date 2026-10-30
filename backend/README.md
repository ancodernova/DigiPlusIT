# ContextFlow AI Backend

FastAPI backend for workspace-scoped meetings, decisions, tasks, knowledge search, and Groq-assisted analysis.

## Local setup

1. Create a Python 3.12 environment.
2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `MONGODB_URL`, `JWT_SECRET`, and (for AI endpoints) `GROQ_API_KEY`.
4. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

OpenAPI documentation is available at `/docs`.

## Main API groups

- `/api/v1/auth` — registration, login, profile, password changes
- `/api/v1/workspaces` — workspace selection and teams
- `/api/v1/meetings` — meetings, participants, and decisions
- `/api/v1/tasks` — task lifecycle, history, and carry-forward
- `/api/v1/knowledge` — workspace documents and text search
- `/api/v1/ai` — meeting analysis and workspace questions
- `/api/v1/dashboard` — metrics and deterministic risk lists
- `/api/v1/transcripts` — paste and file transcript ingestion with polling jobs
- `/api/v1/meetings/{meeting_id}/live-sessions` — consent-aware local mock session lifecycle

## Transcript and live capture configuration

TXT, VTT, SRT, DOCX, and PDF uploads are extracted locally. Audio uploads use Groq's
multipart transcription endpoint with `GROQ_TRANSCRIPTION_MODEL` (normally
`whisper-large-v3-turbo`). The configured upload limit defaults to 25 MB. Files are
stored under `LOCAL_STORAGE_PATH` for local development and are excluded from git.

The `mock` live-session provider is available for local workflow testing only. Zoom,
Google Meet, and Microsoft Teams require an authorized provider integration, OAuth or
bot credentials, webhook validation, and consent; they intentionally return a
configuration error until those adapters are implemented.

## Pinecone and grounded RAG

Pinecone indexing is configuration-gated through `PINECONE_*` and uses the independent
embedding service. The configured index is `contextflow-ai-schema`, a Pinecone document index using the integrated
`llama-text-embed-v2` model, 1024 dimensions, cosine similarity, and `title`/`chunk_text`
fields. Those two fields are the index schema; the remaining source identifiers are
allowlisted metadata (`workspace_id`, `meeting_id`, `transcript_id`, `document_id`,
`task_id`, `source_type`, `source_id`, `chunk_id`, `timestamp`, `speaker`, and
`text_reference`). Do not recreate the index automatically. If creating a new index, obtain its
dimension from the selected embedding provider and verify it before writing.

Set `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE_PREFIX`,
`EMBEDDING_PROVIDER`, and `EMBEDDING_MODEL`. Namespaces are derived only from the
authenticated workspace membership (`<prefix>:<workspace_id>`); client and LLM supplied
workspace IDs are not used for retrieval. Transcript, meeting decision, task, knowledge
document, and Context Passport text is chunked into deterministic IDs. Indexing status is
persisted as pending/processing/completed/failed in MongoDB and a record is marked complete
only after Pinecone confirms the upsert.

`/api/v1/ai/workspace/ask` performs semantic retrieval plus structured task queries and
returns citations. Retrieved content is treated as untrusted evidence. If no semantic
evidence is found, the response marks `insufficient_evidence`.

Whisper is speech-to-text, not an embedding provider. Pinecone document search performs
query embedding inside the configured document index; the embedding service remains
available for provider health checks, batch generation, and vector-index deployments.

Protected workspace routes use a bearer token and optionally an `X-Workspace-ID` header. The first active workspace is selected when that header is omitted.

## Render deployment

Use the included `Dockerfile` or set the start command to:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure the variables listed in `.env.example` in Render. Do not deploy `.env` or commit credentials.
