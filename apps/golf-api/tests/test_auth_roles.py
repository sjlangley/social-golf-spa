from golf_api.permissions import Roles, UserPermissions
from golf_api.security.auth_roles import (
    ROLE_HIERARCHY,
    expand_roles,
    get_effective_permissions,
)


def test_expand_roles_with_hierarchy():
    """Verify admin role inherits writer and reader roles."""
    roles = expand_roles(['admin'], ROLE_HIERARCHY)
    assert Roles.ADMIN in roles
    assert Roles.WRITER in roles
    assert Roles.READER in roles


def test_expand_roles_with_multiple_roles():
    """Verify that multiple roles are expanded correctly."""
    roles = expand_roles(['writer', 'reader'], ROLE_HIERARCHY)
    assert Roles.WRITER in roles
    assert Roles.READER in roles
    assert Roles.ADMIN not in roles


def test_get_effective_permissions(test_user):
    """Verify that effective permissions are calculated correctly."""
    permissions = get_effective_permissions(test_user)
    assert UserPermissions.READ in permissions
    assert UserPermissions.CREATE not in permissions
    assert UserPermissions.EDIT not in permissions
    assert UserPermissions.DELETE not in permissions
