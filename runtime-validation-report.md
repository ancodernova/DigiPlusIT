# ContextFlow AI Runtime Validation Report

## Environment

- Backend: FastAPI application started on `http://127.0.0.1:8000`.
- Frontend: Next.js application started on `http://127.0.0.1:3000`.
- MongoDB Atlas: live demo workspace records were used by the API tests.
- Pinecone: live schema index `contextflow-ai-schema` was used by the RAG smoke test.
- Groq: configured in the local environment; tests distinguish successful calls from unavailable-provider paths.
- Docker: unavailable on this machine, so Docker-based validation was not run.

## Executed checks

| Area | Command/check | Result |
|---|---|---|
| Backend unit/integration suite | `python -m pytest -q` | **8 passed** |
| Backend compilation | `python -m compileall -q app scripts` | **Passed** |
| Backend live API E2E | `python tests/e2e_auth.py`, `python tests/e2e_workspace.py`, `python tests/e2e_rag.py` | **3 passed** |
| Pinecone schema health | Protected diagnostic endpoint and live record lifecycle | **Connected; 1024 dimensions; cosine; expected schema present** |
| Pinecone demo indexing | Idempotent demo seed | **45 records indexed** |
| Frontend TypeScript | `npx tsc --noEmit` | **Passed** |
| Frontend production build | `npm run build` | **Passed** |
| Frontend browser E2E | `npx playwright test` | **3 passed** |

The Python suite emits a pre-existing `RequestsDependencyWarning`; it does not fail the suite. Docker was not available and therefore is not represented as a passing test.

## Browser coverage

The browser suite verifies:

1. Demo login reaches the protected workspace and navigation works.
2. Ask Workspace and meeting capture controls render.
3. Primary application pages return successfully.

The live API suites additionally verify JWT handling, workspace persistence/isolation, Pinecone health, Context Passport retrieval, grounded RAG answers, and source citations.

## Known gaps

- The full 70-route matrix is not a claim that every route was invoked with every role and payload. Routes requiring destructive or provider-specific actions need dedicated fixtures.
- Docker-dependent infrastructure checks were not run because Docker was unavailable.
- Secondary UI mutation flows (for example task approval, passport export, and transcript upload through the browser) remain candidates for additional browser scenarios even though their backend routes and primary pages build successfully.
