from pathlib import Path

import pytest
from sqlalchemy import text

from app.db.session import SessionLocal
from app.rag.embeddings import get_embedding_provider
from app.rag.ingest import ingest_corpus
from tests.conftest import unique_email

PASSWORD = "correct-horse-battery-staple"
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "corpus" / "content"
SOURCES_MD = REPO_ROOT / "corpus" / "sources.md"


def _pgvector_available() -> bool:
    db = SessionLocal()
    try:
        row = db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
        return row is not None
    finally:
        db.close()


def _authed_headers(api_client) -> dict[str, str]:
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    login = api_client.post("/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    api_client.post(
        "/consent",
        json={
            "jurisdiction": "US-CA",
            "is_adult_confirmed": True,
            "other_party_notice_ack": True,
        },
        headers=headers,
    )
    return headers


def test_analyze_red_flag_upload_returns_safety_stop_not_analysis(api_client):
    headers = _authed_headers(api_client)

    upload_response = api_client.post(
        "/upload",
        json={"raw_text": "Alex: reply to me right now or else\nJordan: that's scary, stop"},
        headers=headers,
    )
    assert upload_response.status_code == 201
    thread_id = upload_response.json()["thread_id"]

    analyze_response = api_client.post(
        "/analyze", json={"thread_id": thread_id}, headers=headers
    )
    assert analyze_response.status_code == 200
    body = analyze_response.json()
    assert body["safety_stopped"] is True
    assert body["safety_message"]
    assert body["hypotheses"] == []
    assert body["strategy"] is None


def test_analyze_unknown_thread_returns_404(api_client):
    headers = _authed_headers(api_client)

    response = api_client.post(
        "/analyze",
        json={"thread_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.skipif(
    not _pgvector_available(),
    reason="pgvector extension not installed in this environment (see TASKS.md T1.3)",
)
def test_analyze_happy_path_returns_grounded_response_with_no_raw_pii(api_client):
    # /analyze's retrieval step depends on the corpus already being ingested; don't
    # rely on test execution order picking up another test's side effect for that.
    db = SessionLocal()
    try:
        ingest_corpus(db, CONTENT_DIR, SOURCES_MD, get_embedding_provider())
    finally:
        db.close()

    headers = _authed_headers(api_client)

    raw_text = (
        "Alex: hey, it's Alex here, how's your week going?\n"
        "Jordan: pretty good! just got back from a hike, you?"
    )
    upload_response = api_client.post("/upload", json={"raw_text": raw_text}, headers=headers)
    assert upload_response.status_code == 201
    thread_id = upload_response.json()["thread_id"]

    analyze_response = api_client.post(
        "/analyze", json={"thread_id": thread_id}, headers=headers
    )
    assert analyze_response.status_code == 200
    body = analyze_response.json()

    assert body["safety_stopped"] is False
    assert len(body["hypotheses"]) >= 1
    assert any(h["citations"] for h in body["hypotheses"])
    assert len(body["emotional_reads"]) >= 1
    assert all(r["counter_read"] for r in body["emotional_reads"])
    assert body["strategy"] is not None
    assert len(body["strategy"]["options"]) >= 1

    # No raw PII (the real speaker name) should appear anywhere in the response.
    assert "Alex" not in str(body)
