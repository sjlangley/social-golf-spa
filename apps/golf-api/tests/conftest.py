"""Shared pytest fixtures for API tests."""

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from golf_api.app import app
from golf_api.models.user import User
from golf_api.security.security import get_current_user

TEST_USER_EMAIL = 'test_user@test.org'
TEST_USER_ID = 'test-oid-123'
TEST_USER_NAME = 'Test User'


@pytest.fixture
def test_user():
    """Create a test user for the session."""
    return User(
        email=TEST_USER_EMAIL,
        userid=TEST_USER_ID,
        name=TEST_USER_NAME,
    )


@pytest_asyncio.fixture()
async def async_test_client():
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app), base_url='http://test'
        ) as client:
            yield client


@pytest.fixture
def override_bearer_token_dependency(test_user):
    # Override the verify_api_key dependency for the test, and inject a user
    # with limited permissions (not admin)
    def override_get_current_user() -> User:
        return test_user

    # Apply the override
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Ensure that the override is cleaned up after the test
    yield

    # Clean up the override after the test is done
    app.dependency_overrides.clear()
