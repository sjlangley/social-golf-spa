from fastapi import APIRouter, Depends, Query, Request

from golf_api.constants import DEFAULT_GET_LIMIT, MAX_GET_LIMIT, CollectionNames
from golf_api.models.user import User
from golf_api.permissions import UserPermissions
from golf_api.security.permissions import require_scoped_permission
from golf_api.utils.firestore import FirestoreDB

router = APIRouter(tags=['users'])


@router.get('/', response_description='List all users')
async def list_users(
    db: FirestoreDB,
    limit: int = Query(
        DEFAULT_GET_LIMIT,
        ge=1,
        le=MAX_GET_LIMIT,
        description='Number of users to return',
    ),
    _=Depends(require_scoped_permission(UserPermissions.READ)),
) -> list[User]:
    """List all users."""
    collection = db.collection(CollectionNames.USERS)
    query = collection.limit(limit)
    items: list[User] = []
    async for doc in query.stream():
        data = doc.to_dict()
        if data:
            items.append(User(**data))
    return items
