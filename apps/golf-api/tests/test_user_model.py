"""Tests for the User model."""

from pydantic import ValidationError
import pytest

from golf_api.models.user import User


def test_user_requires_required_fields() -> None:
    with pytest.raises(ValidationError):
        User(email='a@example.com')  # type: ignore[call-arg]


def test_user_allows_missing_email() -> None:
    user = User(userid='abc')
    assert user.email is None


def test_user_allows_optional_name() -> None:
    user = User(email='a@example.com', userid='abc')
    assert user.name is None


def test_user_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        User(email='a@example.com', userid='abc', extra_field='nope')  # type: ignore[call-arg]
