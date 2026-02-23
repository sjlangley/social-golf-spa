"""User roles for authentication and authorization."""

import logging

from golf_api.models.user import User
from golf_api.permissions import Roles, UserPermissions

logger = logging.getLogger(__name__)

# Users can have multiple roles, and roles can inherit from each other.
ROLE_HIERARCHY: dict[Roles, set[Roles]] = {
    Roles.ADMIN: {Roles.WRITER},
    Roles.WRITER: {Roles.READER},
    Roles.READER: set(),
}


# Fine grained role permissions. Permissions get expanded based on the user
# roles and the role hierarchy.
ROLE_PERMISSIONS = {
    Roles.READER: {UserPermissions.READ},
    Roles.WRITER: {UserPermissions.CREATE, UserPermissions.EDIT},
    Roles.ADMIN: {
        UserPermissions.ALL,
    },
}


def expand_roles(
    roles: list[str], hierarchy: dict[Roles, set[Roles]]
) -> set[Roles]:
    """Given a list of roles, return all inherited roles."""
    expanded = set()

    def add_role(role: Roles) -> None:
        if role not in expanded:
            expanded.add(role)
            for inherited in hierarchy.get(role, []):
                add_role(inherited)

    for role_str in roles:
        try:
            role = Roles(role_str)
            add_role(role)
        except ValueError:
            logger.warning('Invalid role string: %s', role_str)

    return expanded


def get_effective_permissions(user: User) -> set[str]:
    """
    Merge permissions from:
    - All roles (with hierarchy)
    - User-level overrides
    """
    roles = expand_roles(user.roles, ROLE_HIERARCHY)

    # Start with role-based permissions
    effective: set[str] = set()
    for role in roles:
        permissions = ROLE_PERMISSIONS.get(role, set())
        if permissions:
            effective.update(permissions)

    # Apply user-specific permission overrides
    overrides = user.permissions

    for perm, allow in overrides.items():
        if allow:
            effective.add(perm)
        else:
            effective.discard(perm)

    return effective
