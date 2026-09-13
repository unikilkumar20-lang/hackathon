import pytest
from app.core.config import settings
from app.core.errors import UnauthorizedException
from app.core.auth import verify_firebase_id_token


def test_missing_auth_header_fails_closed(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "Authorization header" in data["error"]["message"]


def test_invalid_bearer_token(client):
    response = client.get("/api/v1/me", headers={"Authorization": "InvalidPrefix xyz"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_unconfigured_firebase_fails_closed():
    # When testing mock tokens is disabled and Firebase project ID is unset, must fail closed
    original_flag = settings.AUTH_ALLOW_MOCK_TOKENS_FOR_TESTING
    original_project = settings.FIREBASE_PROJECT_ID
    try:
        settings.AUTH_ALLOW_MOCK_TOKENS_FOR_TESTING = False
        settings.FIREBASE_PROJECT_ID = ""
        with pytest.raises(UnauthorizedException) as exc_info:
            verify_firebase_id_token("some-live-id-token")
        assert exc_info.value.code == "FIREBASE_AUTH_UNCONFIGURED"
    finally:
        settings.AUTH_ALLOW_MOCK_TOKENS_FOR_TESTING = original_flag
        settings.FIREBASE_PROJECT_ID = original_project


def test_authenticated_me_upserts_user(client, user_a_headers):
    response = client.get("/api/v1/me", headers=user_a_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["firebase_uid"] == "user-a"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "created_at" in data
