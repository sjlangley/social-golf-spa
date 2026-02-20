"""REST API handler for test purposes."""

from fastapi import APIRouter, Depends, status

from golf_api.models.user import User
from golf_api.security.security import get_current_user

router = APIRouter()


@router.get(
    '',
    response_description='Return the currently authenticated user',
    status_code=status.HTTP_200_OK,
    response_model=User,
    include_in_schema=False,
)
async def get_current_user_test(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user for test purposes."""
    return current_user
