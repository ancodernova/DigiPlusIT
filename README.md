# ContextFlow AI

ContextFlow AI is a workspace-scoped meeting intelligence application. It captures
meeting transcripts, preserves decisions, manages follow-up tasks, indexes knowledge,
and provides grounded workspace questions with source citations.

The repository contains:

- `backend/` - FastAPI, MongoDB Atlas, Groq, and Pinecone services.
- `frontend/` - Next.js application and browser end-to-end tests.
- `runtime-validation-report.md` - the latest validation evidence and known limitations.

## Current status

The current implementation is wired end to end for the primary application flows:

- Authentication and JWT-protected workspace access.
- Workspace-scoped meetings, transcripts, decisions, tasks, and knowledge documents.
- Context Passport retrieval.
- Pinecone schema index integration and grounded RAG citations.
- Demo workspace seeding with deterministic, idempotent records.
- Live API smoke tests and Playwright browser tests.

The latest verified results are:

| Check | Result |
|---|---:|
| Backend pytest suite | 8 passed |
| Backend compilation | Passed |
| Live backend API E2E suites | 3 passed |
| Frontend TypeScript check | Passed |
| Frontend production build | Passed |
| Playwright browser suite | 3 passed |
| Pinecone demo records | 45 indexed |

See [runtime-validation-report.md](./runtime-validation-report.md) for the exact
scope of these checks. Docker-dependent checks were not run because Docker was
unavailable in the validation environment.

## Prerequisites

- Python 3.12
- Node.js 22 or compatible current Node.js release
- MongoDB Atlas or another MongoDB deployment
- Pinecone account and API key for semantic indexing
- Groq API key for meeting analysis, RAG generation, and audio transcription

## Configuration

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the required values in `backend/.env`:

- `MONGODB_URL`
- `MONGODB_DB_NAME`
- `JWT_SECRET`
- `GROQ_API_KEY` for Groq-powered features
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_NAMESPACE_PREFIX`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`

Never commit `.env`, API keys, JWT secrets, or demo passwords. The repository
contains only example configuration files.

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
```

Set `NEXT_PUBLIC_API_URL` to the backend URL when it differs from the default
local API address.

## Start the application

Start the backend in one terminal:

```powershell
cd "C:\Users\Aniket\OneDrive\Desktop\Dev\Hackathon\DigiPlusIT Techhack\contextflow-ai\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
cd "C:\Users\Aniket\OneDrive\Desktop\Dev\Hackathon\DigiPlusIT Techhack\contextflow-ai\frontend"
npm run dev
```

Open:

- Frontend: `http://127.0.0.1:3000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

For a production frontend build:

```powershell
npm run build
npm run start
```

## Demo workspace

The demo seed creates a separate workspace with fictional users, teams, meetings,
transcripts, decisions, tasks, knowledge documents, activity records,
notifications, and a Context Passport. It is designed to be safely rerun:
MongoDB IDs and Pinecone record IDs are deterministic, and the seed only writes
to the dedicated demo workspace.

Run it from `backend/`:

```powershell
python scripts/seed_demo.py
```

To seed MongoDB without calling Pinecone:

```powershell
python scripts/seed_demo.py --skip-pinecone
```

The local demo password is generated and stored in the ignored file
`backend/.demo-credentials`. Do not copy that password into source control or
public documentation. The primary demo email is:

```text
asmiya.sayyed@contextflowdemo.com
```

## Pinecone and RAG

The active Pinecone index is a document index configured with:

- Integrated model: `llama-text-embed-v2`
- Dimension: `1024`
- Similarity metric: `cosine`
- Semantic fields: `title`, `chunk_text`
- Allowlisted metadata: workspace, source, meeting, transcript, document, task,
  chunk, timestamp, speaker, and text-reference identifiers

The backend uses workspace-derived namespaces:

```text
<PINECONE_NAMESPACE_PREFIX>:<workspace_id>
```

The namespace is resolved from the authenticated user's workspace membership.
Client-supplied or LLM-supplied workspace IDs are not trusted for retrieval or
deletion. This prevents cross-workspace vector access.

Indexed source types include:

- Transcript chunks
- Meeting summaries
- Approved decisions
- Approved action items
- Knowledge documents
- Context Passports

Indexing uses deterministic IDs, paragraph-aware chunking, allowlisted metadata,
and persisted job states (`pending`, `processing`, `completed`, and `failed`).
A MongoDB source is marked indexed only after Pinecone confirms the upsert.

Ask Workspace is available at:

```text
POST /api/v1/ai/workspace/ask
```

It combines semantic Pinecone retrieval with structured MongoDB task evidence,
passes grounded context to Groq, returns citations, and reports insufficient
evidence instead of fabricating an answer.

Groq Whisper is used for speech-to-text only. It is not used as an embedding
provider.

## Main API routes

All routes are under `/api/v1`.

| Group | Purpose |
|---|---|
| `/auth` | Registration, login, current profile, and password operations |
| `/workspaces` | Workspace selection, members, teams, and membership |
| `/meetings` | Meeting CRUD, participants, transcripts, decisions, and analysis |
| `/tasks` | Task CRUD, assignment, status, history, and carry-forward |
| `/knowledge` | Knowledge document CRUD, search, linking, and indexing |
| `/ai` | Meeting analysis, suggestions, approval, and Ask Workspace |
| `/dashboard` | Workspace metrics and activity-oriented dashboard data |
| `/transcripts` | Pasted/file transcript ingestion and processing jobs |
| `/live-sessions` | Consent-aware local live-session lifecycle |
| `/context-passports` | Context Passport generation, retrieval, and export |
| `/pinecone` | Protected Pinecone health and schema diagnostics |

The live-session provider is intentionally limited to the local mock provider
unless an authorized Zoom, Google Meet, or Microsoft Teams integration is
configured. Unsupported external providers return an explicit configuration
error rather than pretending to start a live session.

## Testing

Backend tests:

```powershell
cd backend
python -m pytest -q
python -m compileall -q app scripts
```

Frontend type check and production build:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Browser tests require the backend and frontend to be running and a seeded demo
account:

```powershell
cd frontend
npx playwright test
```

The live E2E scripts are in `backend/tests/e2e_auth.py`,
`backend/tests/e2e_workspace.py`, and `backend/tests/e2e_rag.py`. They use the
configured local environment and should only be run against an isolated demo
workspace or test database.

## Security and data isolation

- Passwords are hashed before persistence.
- JWTs are validated on protected routes.
- Workspace membership is checked before workspace data access.
- MongoDB queries include workspace scope where applicable.
- Pinecone namespaces are derived from authorized workspace context.
- Vector metadata is allowlisted and excludes unnecessary sensitive data.
- Secrets are loaded from environment variables and are never returned by
  health/status endpoints.
- Demo data is isolated by a dedicated workspace marker and deterministic IDs.

## Troubleshooting

### Backend cannot connect

Check `MONGODB_URL`, database network access rules, and whether the selected
MongoDB database is reachable from the current machine. Confirm that the
configured JWT secret is non-empty before starting the API.

### Pinecone schema or dimension mismatch

The Pinecone schema is fixed when an integrated index is created. Do not delete
or recreate an existing production index automatically. Verify the configured
index name, integrated model, dimension, metric, and schema fields using the
protected Pinecone diagnostic endpoint.

### Groq is unavailable

AI endpoints return explicit service errors when Groq is not configured or
temporarily unavailable. Core workspace CRUD operations do not require Groq.

### Frontend cannot reach the API

Confirm that the backend is running on the URL configured in
`frontend/.env.local`, then sign in again so the HttpOnly authentication cookie
is present.

## Project documentation

- Backend-specific setup and Pinecone details: [backend/README.md](./backend/README.md)
- Validation evidence and known gaps: [runtime-validation-report.md](./runtime-validation-report.md)
- Example backend environment: [backend/.env.example](./backend/.env.example)
- Example frontend environment: [frontend/.env.example](./frontend/.env.example)
