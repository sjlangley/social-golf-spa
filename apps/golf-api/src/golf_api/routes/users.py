from fastapi import APIRouter, Depends, Query
from google.cloud import firestore

from golf_api.constants import DEFAULT_GET_LIMIT, MAX_GET_LIMIT, CollectionNames
from golf_api.models.user import User
from golf_api.permissions import UserPermissions
from golf_api.security.permissions import require_scoped_permission
from golf_api.utils.firestore import FirestoreDB
from golf_api.utils.firestore_pagination import Page, paginate_next_async

router = APIRouter(tags=['users'])


@router.get('/', response_description='List all users')
async def list_users(
    db: FirestoreDB,  # type: ignore[valid-type]
    limit: int = Query(
        DEFAULT_GET_LIMIT,
        ge=1,
        le=MAX_GET_LIMIT,
        description='Number of users to return',
    ),
    _=Depends(require_scoped_permission(UserPermissions.READ)),
) -> Page[User]:
    """List all users."""
    return await paginate_next_async(
        db=db,
        query=db.collection(CollectionNames.USERS),
        order_by=[('userid', 'asc'), ('__name__', 'asc')],
        page_size=limit,
        model=User,
    )
