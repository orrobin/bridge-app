from tests.conftest import unique_email

PASSWORD = "correct-horse-battery-staple"


def _authed_user(api_client) -> dict[str, str]:
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    login = api_client.post("/auth/login", json={"email": email, "password": PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
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


def test_upload_without_consent_returns_403(api_client):
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    login = api_client.post("/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = api_client.post(
        "/upload", json={"raw_text": "Alex: hi\nJordan: hey"}, headers=headers
    )
    assert response.status_code == 403


def test_upload_parses_and_redacts_chat(api_client):
    headers = _authed_user(api_client)

    raw_text = "Alex: hey, it's Alex, email me at alex@example.com\nJordan: got it!"
    response = api_client.post("/upload", json={"raw_text": raw_text}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["thread_id"]
    assert body["expires_at"]
    turns = body["turns"]
    assert turns[0]["speaker"] == "SPEAKER_1"
    assert turns[1]["speaker"] == "SPEAKER_2"
    assert "Alex" not in str(turns)
    assert "alex@example.com" not in str(turns)
    assert "[EMAIL]" in turns[0]["text"]


def test_malformed_upload_returns_422_not_500(api_client):
    headers = _authed_user(api_client)

    response = api_client.post(
        "/upload", json={"raw_text": "this has no speaker label at all"}, headers=headers
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_empty_upload_returns_422(api_client):
    headers = _authed_user(api_client)

    response = api_client.post("/upload", json={"raw_text": "   "}, headers=headers)
    assert response.status_code == 422
