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
frontend/   Next.js app
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

Purge expired uploaded target-party data (run on a schedule, e.g. daily cron):

```bash
python -m scripts.purge_expired_uploads
```

## Local infrastructure (Postgres + pgvector, Redis)

```bash
docker compose up -d
```

This starts Postgres 16 with the `vector` extension enabled (via `docker/postgres-init/`) on
`localhost:5432` (db/user/password: `bridge`), and Redis on `localhost:6379`.

**No Docker?** A native Postgres 17 works too (e.g. `winget install PostgreSQL.PostgreSQL.17`),
then create the role/db manually:

```sql
CREATE ROLE bridge LOGIN PASSWORD 'bridge';
CREATE DATABASE bridge OWNER bridge;
```

`pgvector` has no Windows prebuilt package — it must be compiled from source, which requires the
MSVC C++ build tools (Visual Studio "Desktop development with C++" workload) to be installed first,
then follow the [pgvector Windows build instructions](https://github.com/pgvector/pgvector#windows).
Everything except the `knowledge_chunks` table/embeddings (Epic 4+) works without it.

## Embeddings

`app/rag/embeddings.py` picks a provider at runtime: if `OPENAI_API_KEY` is set, it uses OpenAI's
hosted embeddings; otherwise it falls back to a deterministic, dependency-free hashing-trick
bag-of-words embedder (no network/API key needed, but not a real semantic model — fine for
development, not for production quality).

Once the DB is reachable (`docker compose up -d` or a native Postgres, above), apply migrations
and ingest the seed corpus:

```bash
alembic upgrade head
python -m scripts.ingest_corpus
```

## Eval

`python -m scripts.run_eval` prints an offline eval report: retrieval Recall@1/3/5 against a
hand-labeled golden set (`app/rag/golden_set.py`) and a citation-accuracy spot check (does every
citation the Analyst/Strategy agents emit reference a real, licensed corpus source). It's a
report, not a pass/fail gate — it runs as a non-blocking CI step (`continue-on-error`) so a dip in
retrieval quality is visible without blocking merges. Requires the corpus already ingested
(above) against a pgvector-enabled Postgres.

## Agents: Claude API credits

`app/agents/safety.py`, `analyst.py`, `eq.py`, and `strategy.py` each ship a deterministic
heuristic provider (active by default, no API costs) and a real Claude-based provider
(`Claude*Provider`, fully implemented but inactive). The Anthropic API key configured here is
valid but the console account has no credit balance — a Claude subscription (e.g. Claude Code)
does **not** cover separate Messages API billing. Once credits exist, set
`USE_LLM_SAFETY_CLASSIFIER=true` and `USE_LLM_AGENTS=true` in `.env` to switch over; nothing else
needs to change.

## Frontend — local setup

Requires Node.js (tested on 24.x).

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000** — not `127.0.0.1:3000`. Next.js 16's dev server blocks the
HMR/webpack websocket for origins other than `localhost` by default (`allowedDevOrigins`), and
without it connecting, event handling silently breaks (forms fall back to native, unintercepted
submission). The backend must be running (`uvicorn app.main:app`) with CORS allowing
`http://localhost:3000` (already the default in `app/core/config.py`).

Covers: signup/login, the 18+/jurisdiction/other-party consent screen, pasting a chat, and a
results view with confidence-banded hypotheses, emotional reads (each with a counter-read), and
cited reply options. Manually verified end-to-end in a real browser against the local backend,
including the safety-stop path (red-flag input never reaches analysis). The full "grounded
results with citations" path additionally needs the corpus ingested into a pgvector-enabled
Postgres (see above) — blocked on this dev machine same as the backend retrieval tests, verified
in CI instead.

## Status

Under active, incremental development — see [`TASKS.md`](TASKS.md) for what's built vs. planned.
