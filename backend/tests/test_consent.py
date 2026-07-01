from tests.conftest import unique_email

PASSWORD = "correct-horse-battery-staple"


def _signup_and_login(api_client) -> str:
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    login = api_client.post("/auth/login", json={"email": email, "password": PASSWORD})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_analyze_without_auth_returns_401(api_client):
    response = api_client.post("/analyze")
    assert response.status_code == 401


def test_analyze_without_consent_returns_403_naming_required_step(api_client):
    token = _signup_and_login(api_client)

    response = api_client.post("/analyze", headers=_auth_headers(token))
    assert response.status_code == 403
    assert "consent" in response.json()["detail"].lower()
    assert "/consent" in response.json()["detail"]


def test_analyze_with_valid_consent_is_accepted(api_client):
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

    analyze_response = api_client.post("/analyze", headers=headers)
    assert analyze_response.status_code == 200


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
