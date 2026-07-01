from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models.user import User
from tests.conftest import unique_email

PASSWORD = "correct-horse-battery-staple"


def test_signup_then_login_succeeds(api_client):
    email = unique_email()

    signup_response = api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    assert signup_response.status_code == 201
    assert signup_response.json()["email"] == email

    login_response = api_client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_password_is_never_stored_plaintext(api_client):
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        assert user.hashed_password != PASSWORD
        assert verify_password(PASSWORD, user.hashed_password)
    finally:
        db.close()


def test_login_with_wrong_password_returns_401(api_client):
    email = unique_email()
    api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})

    response = api_client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401


def test_login_with_unknown_email_returns_401(api_client):
    response = api_client.post(
        "/auth/login", json={"email": unique_email(), "password": PASSWORD}
    )
    assert response.status_code == 401


def test_duplicate_signup_returns_400(api_client):
    email = unique_email()
    first = api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    assert first.status_code == 201

    second = api_client.post("/auth/signup", json={"email": email, "password": PASSWORD})
    assert second.status_code == 400
