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

Protected workspace routes use a bearer token and optionally an `X-Workspace-ID` header. The first active workspace is selected when that header is omitted.

## Render deployment

Use the included `Dockerfile` or set the start command to:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Configure the variables listed in `.env.example` in Render. Do not deploy `.env` or commit credentials.
