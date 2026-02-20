"""Tests for health check endpoint."""

import pytest


@pytest.mark.asyncio
@pytest.mark.usefixtures('override_bearer_token_dependency')
async def test_health_endpoint_overrride(async_test_client, test_user):
    """Test that health endpoint returns a 200 OK with correct content."""
    response = await async_test_client.get('/api/test')
    assert response.status_code == 200
    assert response.json() == {
        'email': test_user.email,
        'userid': test_user.userid,
        'name': test_user.name,
    }


@pytest.mark.asyncio
async def test_health_endpoint(async_test_client, test_user):
    """Test that health endpoint returns a 200 OK with correct content."""
    response = await async_test_client.get('/api/test')
    assert response.status_code == 401
