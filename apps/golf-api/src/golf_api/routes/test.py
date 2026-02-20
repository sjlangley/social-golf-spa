"""REST API handler for test purposes."""

from fastapi import APIRouter, Depends, status

from golf_api.models.user import User
from golf_api.security.security import get_current_user

router = APIRouter()


@router.get(
    '',
    response_description='Return HTTP Status Code 200 (OK)',
    status_code=status.HTTP_200_OK,
    response_model=User,
    include_in_schema=False,
)
async def get_health(current_user: User = Depends(get_current_user)) -> User:
    """Perform a health check and return the service status."""
    return current_user
