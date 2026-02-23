from typing import Callable

from fastapi import Depends, HTTPException, status

from golf_api.models.user import User
from golf_api.security.auth_roles import get_effective_permissions
from golf_api.security.security import get_current_user


def require_scoped_permission(scope: str) -> Callable:
    """Require a specific role for the user."""

    async def dependency(user: User = Depends(get_current_user)):
        """Dependency to check if the user has the required role."""
        permissions = get_effective_permissions(user)
        if scope in permissions or f'{scope.split(":")[0]}:*' in permissions:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'User does not have the required scope: {scope}',
        )

    return dependency
