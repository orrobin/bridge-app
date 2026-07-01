# Bridge

A private, evidence-grounded RAG communication coach for early-stage dating conversations —
helping users understand their own patterns and communicate authentically, not "win" dates
through manipulation.

Full product/architecture rationale: [`docs/Software-Architecture-Document.md`](docs/Software-Architecture-Document.md).
MVP task breakdown and acceptance criteria: [`TASKS.md`](TASKS.md).

## What this is / isn't

- This is a coaching tool that helps you reflect on your own communication, grounded in cited
  relationship-science sources — not an "attraction score" or pickup-artist scripting engine.
- It does not build a persistent profile of the other person in your conversation; only the
  user's own patterns are retained, with consent.
- It is not therapy or medical advice. If a conversation shows signs of abuse, coercion, or
  involves a minor, the app stops analysis and surfaces safety resources instead.
- Text-only inference of attraction/emotion is low-validity. Outputs are shown as hypotheses
  with confidence bands and counter-evidence, never as certainties.

See SAD §0 and §1.5 for the full ethical rationale.

## Repo layout

```
backend/    FastAPI app (API, agents, RAG pipeline, DB models)
frontend/   Next.js app (added in Epic 9)
corpus/     Seed knowledge sources + licensing ledger (sources.md)
docs/       Architecture document
```

## Backend — local setup

Requires Python >= 3.11.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\Activate.ps1 in PowerShell
pip install -e ".[dev]"
cp .env.example .env
```

Run the API:

```bash
uvicorn app.main:app --reload
curl http://127.0.0.1:8000/health   # {"status": "ok"}
```

Run tests and lint:

```bash
pytest -q
ruff check .
```

## Local infrastructure (Postgres + pgvector, Redis)

```bash
docker compose up -d
```

This starts Postgres 16 with the `vector` extension enabled (via `docker/postgres-init/`) on
`localhost:5432` (db/user/password: `bridge`), and Redis on `localhost:6379`.

## Status

Under active, incremental development — see [`TASKS.md`](TASKS.md) for what's built vs. planned.
