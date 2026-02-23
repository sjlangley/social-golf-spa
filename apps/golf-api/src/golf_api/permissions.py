from enum import StrEnum


class Roles(StrEnum):
    """Enum for the roles in the system."""

    ADMIN = 'admin'
    WRITER = 'writer'
    READER = 'reader'


class UserPermissions(StrEnum):
    """Enum for the permissions for the users API."""

    READ = 'users:read'
    CREATE = 'users:create'
    EDIT = 'users:edit'
    DELETE = 'users:delete'
    ALL = 'users:*'
