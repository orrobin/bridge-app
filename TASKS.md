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
- [x] T1.1 SQLAlchemy models: `User`, `ConsentRecord`, `ConversationThread`, `UserProfile`, `AuditLogEntry`.
      AC: models import cleanly; Alembic autogenerate produces a migration with these tables.
      Verified: local PostgreSQL 17 (installed via winget), `alembic revision --autogenerate` produced the migration.
- [x] T1.2 Alembic wired to a real Postgres.
      AC: `alembic upgrade head` succeeds against a fresh DB; downgrade also works.
      Verified: `alembic upgrade head` / `downgrade base` / `upgrade head` again all succeeded against local Postgres 17 (`bridge` db); `\dt` confirms all 5 tables.
- [x] T1.3 pgvector table for corpus embeddings (`KnowledgeChunk`).
      AC: table has a `vector` column of a fixed dimension; a raw insert+cosine-similarity query returns the nearest row in a test.
      Verified in CI (not locally): local Windows dev can't compile pgvector (no MSVC build tools with
      elevation available), but CI runs `pgvector/pgvector:pg16`, applies both migrations, and
      `tests/test_knowledge_vector.py::test_cosine_similarity_returns_nearest_row` passed there
      (run 28515000860: "11 passed, 1 warning", 0 skipped) -- confirming insert + cosine-distance
      ordering returns the nearest row. The test self-skips locally when the extension is absent.
      To also verify locally: from an elevated terminal, install the "Desktop development with C++"
      workload, build pgvector against this Postgres 17 install, then `alembic upgrade head`.

## Epic 2 — Auth, accounts & consent
- [x] T2.1 User signup/login (email+password, hashed, JWT session).
      AC: `/auth/signup` and `/auth/login` work end-to-end in a test; passwords never stored plaintext; invalid login returns 401.
      Verified: 5 tests in `tests/test_auth.py` passing against real Postgres (signup/login round-trip,
      hashed-not-plaintext check, wrong-password 401, unknown-email 401, duplicate-signup 400).
- [x] T2.2 18+ + jurisdiction + consent capture (other-party non-consent notice).
      AC: consent must be recorded (jurisdiction + timestamp + notice copy) before any `/analyze` call is accepted; missing consent -> 403 naming the required step.
      Verified: 4 tests in `tests/test_consent.py` — no auth -> 401, no consent -> 403 naming `/consent`,
      valid consent -> 200 on a placeholder `/analyze` (full pipeline lands in Epic 8), incomplete
      acknowledgement -> 400.

## Epic 3 — Upload & redaction
- [x] T3.1 Chat upload endpoint (pasted text / WhatsApp export first).
      AC: parser splits into turns with speaker labels; malformed input returns 422 with a helpful message, not a 500.
      Verified: `tests/test_chat_parser.py` (6 tests: generic + WhatsApp formats, multi-line messages,
      empty/unparseable/single-speaker error cases) and `tests/test_upload.py` 422 cases via `POST /upload`.
- [x] T3.2 Redaction pass (names/phone/email/handles) before persistence or LLM calls.
      AC: unit tests show PII patterns replaced with placeholders; redacted text, not raw text, is what gets stored/logged.
      Verified: `tests/test_redaction.py` (5 tests) plus `test_upload_parses_and_redacts_chat` confirms
      the DB-persisted response only ever contains redacted turns (`SPEAKER_n` + `[EMAIL]`/`[PHONE]`/
      `[HANDLE]`/`[URL]` placeholders) -- raw text is never stored.
- [x] T3.3 TTL on raw/target-party data.
      AC: uploaded raw target-party rows carry `expires_at`; a cleanup job deletes expired rows; test proves expired rows are purged.
      Verified: `UploadedChatData.expires_at` set on every upload (30-day TTL, `app/core/retention.py`);
      `scripts/purge_expired_uploads.py` (run via cron/scheduled task, documented in README) calls
      `purge_expired_uploads()`, confirmed against real Postgres; `tests/test_retention.py` proves an
      expired row is deleted while a non-expired row survives.

## Epic 4 — Knowledge corpus & ingestion (small, MVP-sized)
- [x] T4.1 Seed corpus (5-15 items) of open-access/CC/first-party-written short explainers, license-tagged.
      AC: `corpus/sources.md` ledger lists each item + license + attribution; ingestion refuses to load anything missing a license tag.
      Verified: 8 original first-party explainers in `corpus/content/` (bids for connection,
      attachment styles, active listening, NVC basics, reading disinterest, positivity ratio,
      boundaries/consent, repair after miscommunication) -- no copyrighted book/course text, only
      original writing informed by publicly described concepts, per SAD Phase 3.1. All 8 listed in
      `corpus/sources.md`; `test_all_seed_content_files_are_listed_in_the_ledger` and
      `ingest_corpus()`'s `CorpusError` on an unlisted id both verified in `tests/test_corpus.py`.
      Embeddings: no embedding API key/network path was available for a genuinely free option
      (Hugging Face + Voyage AI both blocked on this network, OpenAI is reachable but not free) --
      shipped a deterministic, dependency-free hashing-trick bag-of-words embedder
      (`app/rag/embeddings.py::HashingBagOfWordsEmbedder`) behind an `EmbeddingProvider` interface,
      with a real `OpenAIEmbedder` already implemented and auto-selected once `OPENAI_API_KEY` is set.
- [x] T4.2 Chunking + metadata + embedding + load into pgvector.
      AC: ingestion script populates `KnowledgeChunk` rows with embeddings; a smoke query retrieves the relevant chunk in the top 3.
      Verified in CI (pgvector blocked locally, same as T1.3): `scripts/ingest_corpus.py` /
      `app/rag/ingest.py::ingest_corpus` is idempotent (replaces a source's chunks on re-run);
      `tests/test_ingest.py::test_ingest_corpus_then_smoke_query_finds_relevant_chunk` ingests all 8
      docs and confirms a disinterest-themed query's top-3 nearest chunks include
      `reading-disinterest-signals` (skips locally, runs for real in CI's pgvector Postgres).

## Epic 5 — Retrieval pipeline (MVP-scoped hybrid)
- [x] T5.1 Vector search (pgvector) + Postgres full-text + Reciprocal Rank Fusion.
      AC: hybrid results outrank pure-vector-only results on a small hand-labeled golden set (>=3 queries).
      Verified in CI (pgvector blocked locally, same as T1.3): `tests/test_hybrid_retrieval.py`,
      5-query golden set of natural-language questions (deliberately not sharing exact vocabulary
      with their target doc, since that's where the crude hash embedder needs lexical's help);
      asserts hybrid's mean reciprocal rank beats vector-only's and no query regresses. Lexical
      search uses OR-joined tsquery terms (not plainto_tsquery's implicit AND), since natural
      questions rarely share every content word with a relevant chunk.
- [x] T5.2 Basic query rewrite (expand a vague question using the conversation window).
      AC: fixture-based test shows the rewritten query includes key terms absent from the raw question.
      Verified: `tests/test_query_rewrite.py` (3 tests). Deterministic heuristic (salient terms from
      recent turns, no LLM call) -- kept dependency-free since it's a mechanical text expansion, not
      reasoning; LLM usage is reserved for Epics 6-7 where real reasoning is required.
- [x] T5.3 Context compression (trim to relevant sentences) before generation.
      AC: token count of assembled context is reduced vs. raw top-k concat, without dropping the golden-answer sentence.
      Verified: `tests/test_compression.py` -- extractive, term-overlap-scored sentence selection
      confirmed to shrink token count while preserving the query-relevant sentence.

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
