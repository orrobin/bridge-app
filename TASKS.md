# Bridge — MVP Task Breakdown

Source of truth for MVP scope: `docs/Software-Architecture-Document.md`, Phase 9 ("MVP" row).
Tasks are built in order, epic by epic. Check a box when its acceptance criteria (AC) is verified
by an actual command/test run, not just "looks right."

## Epic 0 — Project scaffolding & CI
- [x] T0.1 Repo init: folder structure, `.gitignore`, `README.md`, `LICENSE`.
      AC: `git log` has an initial commit; pushed to `origin main` on GitHub; repo is private.
- [x] T0.2 Backend skeleton: FastAPI app boots, `/health` returns 200.
      AC: `uvicorn app.main:app` runs locally; `GET /health` -> `{"status":"ok"}`; one pytest passes.
- [x] T0.3 Docker Compose for Postgres+pgvector and Redis.
      AC: `docker compose up` gives a reachable Postgres with the `vector` extension enabled and Redis; documented in README.
- [x] T0.4 CI workflow (GitHub Actions): install deps, run lint (ruff) + tests on every push/PR.
      AC: workflow file present, passes on first push (green check on GitHub).

## Epic 1 — Data layer & migrations
- [ ] T1.1 SQLAlchemy models: `User`, `ConsentRecord`, `ConversationThread`, `UserProfile`, `AuditLogEntry`.
      AC: models import cleanly; Alembic autogenerate produces a migration with these tables.
- [ ] T1.2 Alembic wired to the Compose Postgres.
      AC: `alembic upgrade head` succeeds against a fresh DB; downgrade also works.
- [ ] T1.3 pgvector table for corpus embeddings (`KnowledgeChunk`).
      AC: table has a `vector` column of a fixed dimension; a raw insert+cosine-similarity query returns the nearest row in a test.

## Epic 2 — Auth, accounts & consent
- [ ] T2.1 User signup/login (email+password, hashed, JWT session).
      AC: `/auth/signup` and `/auth/login` work end-to-end in a test; passwords never stored plaintext; invalid login returns 401.
- [ ] T2.2 18+ + jurisdiction + consent capture (other-party non-consent notice).
      AC: consent must be recorded (jurisdiction + timestamp + notice copy) before any `/analyze` call is accepted; missing consent -> 403 naming the required step.

## Epic 3 — Upload & redaction
- [ ] T3.1 Chat upload endpoint (pasted text / WhatsApp export first).
      AC: parser splits into turns with speaker labels; malformed input returns 422 with a helpful message, not a 500.
- [ ] T3.2 Redaction pass (names/phone/email/handles) before persistence or LLM calls.
      AC: unit tests show PII patterns replaced with placeholders; redacted text, not raw text, is what gets stored/logged.
- [ ] T3.3 TTL on raw/target-party data.
      AC: uploaded raw target-party rows carry `expires_at`; a cleanup job deletes expired rows; test proves expired rows are purged.

## Epic 4 — Knowledge corpus & ingestion (small, MVP-sized)
- [ ] T4.1 Seed corpus (5-15 items) of open-access/CC/first-party-written short explainers, license-tagged.
      AC: `corpus/sources.md` ledger lists each item + license + attribution; ingestion refuses to load anything missing a license tag.
- [ ] T4.2 Chunking + metadata + embedding + load into pgvector.
      AC: ingestion script populates `KnowledgeChunk` rows with embeddings; a smoke query retrieves the relevant chunk in the top 3.

## Epic 5 — Retrieval pipeline (MVP-scoped hybrid)
- [ ] T5.1 Vector search (pgvector) + Postgres full-text + Reciprocal Rank Fusion.
      AC: hybrid results outrank pure-vector-only results on a small hand-labeled golden set (>=3 queries).
- [ ] T5.2 Basic query rewrite (expand a vague question using the conversation window).
      AC: fixture-based test shows the rewritten query includes key terms absent from the raw question.
- [ ] T5.3 Context compression (trim to relevant sentences) before generation.
      AC: token count of assembled context is reduced vs. raw top-k concat, without dropping the golden-answer sentence.

## Epic 6 — Safety & Ethics agent (pre + post gate)
- [ ] T6.1 Pre-screen classifier/rules on upload (minors, abuse, coercion, self-harm).
      AC: red-team fixture set (>=10 adversarial) all correctly flagged; >=10 benign fixtures all pass; false-block rate reported.
- [ ] T6.2 Post-gate on generated output (blocks manipulation/pushy-past-disinterest language).
      AC: fixture set of manipulative draft replies all blocked/rewritten; a benign reply passes untouched.
- [ ] T6.3 Every Safety decision written to the audit log.
      AC: every allow/block/escalate decision has a row in `AuditLogEntry` with input hash, decision, reason.

## Epic 7 — Analyst / EQ / Strategy agents + Orchestrator (single-pass)
- [ ] T7.1 Orchestrator: deterministic call sequence (Safety pre -> Analyst+EQ+Profile parallel -> Strategy -> Meeting-lite -> Safety post).
      AC: integration test drives a redacted sample chat end-to-end and asserts call order via logged trace.
- [ ] T7.2 Conversation Analyst agent: confidence-banded hypotheses, grounded via Retrieval.
      AC: output includes >=1 citation; no bare numeric certainty ("scores as truth") output.
- [ ] T7.3 Emotional Intelligence agent: possible reads + explicit counter-read.
      AC: every emotional-read output includes a counter-hypothesis field, enforced by schema (not optional).
- [ ] T7.4 Dating Strategy agent: 2-3 authentic reply options + reasoning + citations; refuses to push past disinterest.
      AC: disinterest fixture -> no "keep pursuing" option; mutual-signal fixture -> includes a graceful meeting-suggestion option.

## Epic 8 — API surface tying it together
- [ ] T8.1 `POST /analyze`: upload -> consent-check -> redact -> orchestrate -> grounded, cited response.
      AC: full happy-path integration test (signup -> consent -> analyze) returns a response with citations and no raw PII; red-flag fixture returns the safety-stop response instead of an analysis.

## Epic 9 — Minimal frontend
- [ ] T9.1 Next.js app: login/signup, consent screen, paste-or-upload chat, results view with citations/confidence bands.
      AC: manually driven through the browser end-to-end against the local backend; no raw PII visible if redaction worked.

## Epic 10 — Eval scaffolding & polish
- [ ] T10.1 Golden-set offline eval script (retrieval recall@k, citation-accuracy spot check).
      AC: eval command prints recall@k and a citation-accuracy percentage on the golden set.
- [ ] T10.2 README with setup, running locally, running tests, running eval, and an ethics note.
      AC: a fresh clone + README steps gets a new dev to a passing `pytest` and a working `/health` locally.
