"""Shared pytest fixtures for API tests."""

from asgi_lifespan import LifespanManager
from fake_firestore import AsyncFakeFirestoreClient
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from golf_api.app import app
from golf_api.models.user import User
from golf_api.permissions import UserPermissions
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
        permissions={UserPermissions.READ: True},
    )


@pytest_asyncio.fixture
async def add_user_to_firestore(firestore_client, test_user):
    """Add the test user to Firestore."""
    # This is needed for the endpoint to return the user data, since it
    # fetches from Firestore. The auth override only bypasses the auth check,
    # it doesn't change the fact that the endpoint still needs to fetch the user
    # from Firestore.
    user_data = test_user.model_dump()
    user_data['__name__'] = user_data.get('userid', 'unknown')
    await (
        firestore_client.collection('users')
        .document(test_user.userid)
        .set(user_data)
    )


@pytest_asyncio.fixture
async def add_admin_user_to_firestore(firestore_client, test_user):
    """Add the test user to Firestore with admin role."""
    # This is needed for the endpoint to return the user data, since it
    # fetches from Firestore. The auth override only bypasses the auth check,
    # it doesn't change the fact that the endpoint still needs to fetch the user
    # from Firestore.
    user_data = test_user.model_dump()
    user_data['roles'] = ['admin']
    user_data['__name__'] = user_data.get('userid', 'unknown')
    await (
        firestore_client.collection('users')
        .document(test_user.userid)
        .set(user_data)
    )


@pytest.fixture
def firestore_client():
    """Create a Firestore client for testing."""
    client = AsyncFakeFirestoreClient()
    if not hasattr(client, 'close'):
        # pyrefly: ignore [missing-attribute]
        client.close = lambda: None
    return client


@pytest_asyncio.fixture()
async def async_test_client(firestore_client):
    async with LifespanManager(app):
        # Replace the real Firestore client with the fake one
        # This must happen after lifespan starts but before tests run
        original_client = app.state.db_client
        app.state.db_client = firestore_client

        async with AsyncClient(
            transport=ASGITransport(app), base_url='http://test'
        ) as client:
            yield client

        # Restore original client
        app.state.db_client = original_client


@pytest.fixture
def override_bearer_token_dependency(test_user):
    # Override the get_current_user dependency for the test and inject the
    # test_user instance as the authenticated user.
    def override_get_current_user() -> User:
        return test_user

    # Apply the override
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Ensure that the override is cleaned up after the test
    yield

    # Clean up the specific override after the test is done
    app.dependency_overrides.pop(get_current_user, None)
