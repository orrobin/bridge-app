import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def api_client() -> TestClient:
    return client


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex}@example.com"
