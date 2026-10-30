# ContextFlow AI

ContextFlow AI is a workspace-scoped meeting intelligence platform that turns
conversation into searchable context, accountable work, and grounded team
continuity.

## Live application

**Frontend:** [frontend-omega-wine-55.vercel.app](http://frontend-omega-wine-55.vercel.app/)

## What I built

### Meeting intelligence

- Meeting creation and workspace-scoped meeting management.
- Transcript capture through pasted text and supported file uploads.
- Support for TXT, Markdown, VTT, SRT, DOCX, and PDF transcript files.
- Consent-aware transcript processing.
- Meeting participants, summaries, decisions, action items, and analysis.
- Deterministic transcript chunking and source references.

### Workspace collaboration

- JWT-based registration, login, and protected API access.
- Workspace membership and active workspace selection.
- Role-aware access for administrators, managers, and members.
- Teams, team members, user profiles, notifications, and activity records.
- Strict tenant isolation across MongoDB records and Pinecone namespaces.

### Task and decision management

- Task creation, assignment, priorities, statuses, deadlines, and blockers.
- Task history and status transitions.
- Carry-forward support that preserves the original task ID and prevents
  duplicate tasks.
- Decision and AI-suggestion approval workflows.
- Dashboard metrics for meetings, open work, completed work, and blocked work.

### Context Passports

- Context Passport generation from workspace meetings, decisions, tasks, and
  knowledge.
- Passport retrieval by workspace.
- Markdown export for handovers and continuity between team members.

### Knowledge base

- Workspace knowledge document creation, retrieval, update, deletion, and search.
- Knowledge documents linked to meeting and workspace context.
- Automatic indexing and cleanup when source documents change or are removed.

### Pinecone semantic search and RAG

- Pinecone integrated-inference index using `llama-text-embed-v2`.
- 1024-dimensional embeddings with cosine similarity.
- Schema fields for `title` and `chunk_text`.
- Allowlisted metadata for workspace, meeting, transcript, document, task,
  source, chunk, timestamp, speaker, and text references.
- Deterministic vector IDs for idempotent indexing and re-indexing.
- Workspace-derived namespaces to prevent cross-tenant retrieval.
- Semantic retrieval combined with structured MongoDB task evidence.
- Groq-grounded answers with source citations.
- Insufficient-evidence responses instead of fabricated answers.

### AI and transcription services

- Groq meeting analysis and workspace question answering.
- Groq Whisper audio transcription support.
- Independent embedding-service abstraction.
- Explicit provider error handling for unavailable AI services.
- Background indexing jobs with `pending`, `processing`, `completed`, and
  `failed` states.

### Frontend application

The Next.js frontend includes:

- Authentication and registration screens.
- Workspace dashboard.
- Meetings list, search, capture, transcript, and analysis surfaces.
- Tasks and knowledge base views.
- Ask Workspace interface with answer citations.
- Context Passport screens.
- Activity, settings, profile, security, team, and integration views.
- Responsive navigation and shared application shell.
- HttpOnly authentication cookie handling through server-side API proxies.

### Demo workspace

An idempotent demo seed script creates an isolated fictional workspace with:

- 7 fictional users and workspace memberships.
- 3 teams.
- 8 meetings and transcripts.
- Meeting summaries and approved decisions.
- 24 tasks with varied statuses, priorities, deadlines, blockers, and
  carry-forward examples.
- Knowledge documents, activity logs, notifications, and a Context Passport.
- 45 Pinecone records indexed from demo workspace content.

The primary demo email is:

```text
asmiya.sayyed@contextflowdemo.com
```

The generated demo password is stored locally in the ignored file
`backend/.demo-credentials`.

## Architecture

```text
Next.js frontend
        |
        v
FastAPI REST API
   |          |          |
   v          v          v
MongoDB     Groq      Pinecone
records     AI        semantic index
```

- MongoDB stores users, workspaces, meetings, transcripts, tasks, decisions,
  documents, indexing jobs, activity, notifications, and passports.
- Pinecone stores searchable transcript and workspace-context chunks.
- Groq performs meeting analysis, grounded answer generation, and audio
  transcription.
- The frontend communicates with the backend through authenticated API routes.

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

## Seed the demo workspace

The demo seed is safely rerunnable. MongoDB IDs and Pinecone record IDs are
deterministic, and writes are restricted to the dedicated demo workspace.

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
public documentation.

## Pinecone configuration

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

## API route groups

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

## Validation

The completed implementation was validated with:

| Check | Result |
|---|---:|
| Backend pytest suite | 8 passed |
| Backend Python compilation | Passed |
| Live backend API E2E suites | 3 passed |
| Frontend TypeScript check | Passed |
| Frontend production build | Passed |
| Playwright browser suite | 3 passed |
| Pinecone demo indexing | 45 records |

## Related documentation

- Backend-specific setup and Pinecone details: [backend/README.md](./backend/README.md)
- Validation evidence: [runtime-validation-report.md](./runtime-validation-report.md)
- Example backend environment: [backend/.env.example](./backend/.env.example)
- Example frontend environment: [frontend/.env.example](./frontend/.env.example)
