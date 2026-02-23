"""Tests for api test endpoint."""

import pytest


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    'override_bearer_token_dependency', 'add_admin_user_to_firestore'
)
async def test_get_user(async_test_client, test_user):
    """Test that /api/test returns a 200 OK with correct content when auth is
    overridden.
    """
    response = await async_test_client.get('/api/v1/users/')
    assert response.status_code == 200
    data = response.json()
    items = data.get('items')
    assert items is not None
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]['email'] == test_user.email
    assert items[0]['userid'] == test_user.userid
    assert items[0]['name'] == test_user.name


@pytest.mark.asyncio
async def test_get_user_not_authorized(
    async_test_client, add_user_to_firestore
):
    """Test that /api/test returns a 401 Unauthorized when auth is not
    overridden.
    """
    response = await async_test_client.get('/api/v1/users/')
    assert response.status_code == 401
