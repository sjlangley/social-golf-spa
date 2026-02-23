"""Application Constants."""

from enum import StrEnum

DEFAULT_GET_LIMIT = 50
MAX_GET_LIMIT = 100


class CollectionNames(StrEnum):
    """Firestore collection names."""

    USERS = 'users'
