"""Tests for authentication dependency helpers."""

from fastapi.security import HTTPAuthorizationCredentials
import pytest

from golf_api.enums import Environment
from golf_api.models.user import User
from golf_api.security import security as security_module


@pytest.mark.asyncio
async def test_get_current_user_bypasses_auth_in_local_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
    test_user: User,
    firestore_client,
) -> None:
    monkeypatch.setattr(security_module.settings, 'auth_disabled', True)
    monkeypatch.setattr(
        security_module.settings, 'environment', Environment.LOCAL
    )

    creds = HTTPAuthorizationCredentials(
        scheme='Bearer', credentials='token-123'
    )

    user = await security_module.get_current_user(
        db=firestore_client, token=creds
    )
    assert user.email == 'anonymous'


@pytest.mark.asyncio
async def test_get_current_user_calls_verify_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
    firestore_client,
) -> None:
    monkeypatch.setattr(security_module.settings, 'auth_disabled', False)
    monkeypatch.setattr(
        security_module.settings, 'environment', Environment.PRODUCTION
    )

    expected_user = User(email='u@example.com', userid='user-1', name='User')

    async def fake_verify_bearer_token(token: str) -> User:
        assert token == 'token-123'
        return expected_user

    monkeypatch.setattr(
        security_module, 'verify_bearer_token', fake_verify_bearer_token
    )

    creds = HTTPAuthorizationCredentials(
        scheme='Bearer', credentials='token-123'
    )
    user = await security_module.get_current_user(
        db=firestore_client, token=creds
    )

    assert user == expected_user
