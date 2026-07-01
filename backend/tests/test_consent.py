import uuid

from tests.conftest import unique_email

PASSWORD = "correct-horse-battery-staple"


def _signup_and_login(api_client) -> str:
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    login = api_client.post("/auth/login", json={"email": email, "password": PASSWORD})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _dummy_analyze_body() -> dict[str, str]:
    return {"thread_id": str(uuid.uuid4())}


def test_analyze_without_auth_returns_401(api_client):
    response = api_client.post("/analyze", json=_dummy_analyze_body())
    assert response.status_code == 401


def test_analyze_without_consent_returns_403_naming_required_step(api_client):
    token = _signup_and_login(api_client)

    response = api_client.post(
        "/analyze", json=_dummy_analyze_body(), headers=_auth_headers(token)
    )
    assert response.status_code == 403
    assert "consent" in response.json()["detail"].lower()
    assert "/consent" in response.json()["detail"]


def test_analyze_with_valid_consent_passes_the_consent_gate(api_client):
    token = _signup_and_login(api_client)
    headers = _auth_headers(token)

    consent_response = api_client.post(
        "/consent",
        json={
            "jurisdiction": "US-CA",
            "is_adult_confirmed": True,
            "other_party_notice_ack": True,
        },
        headers=headers,
    )
    assert consent_response.status_code == 201

    # Consent passes, so it proceeds to look for the thread rather than blocking
    # with a 403 -- full end-to-end analysis is covered in tests/test_analyze.py.
    analyze_response = api_client.post(
        "/analyze", json=_dummy_analyze_body(), headers=headers
    )
    assert analyze_response.status_code == 404


def test_consent_rejects_missing_acknowledgements(api_client):
    token = _signup_and_login(api_client)
    headers = _auth_headers(token)

    response = api_client.post(
        "/consent",
        json={
            "jurisdiction": "US-CA",
            "is_adult_confirmed": False,
            "other_party_notice_ack": True,
        },
        headers=headers,
    )
    assert response.status_code == 400
