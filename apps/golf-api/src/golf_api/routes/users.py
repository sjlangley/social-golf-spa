from enum import StrEnum

from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1.field_path import FieldPath

from golf_api.constants import (
    DEFAULT_GET_LIMIT,
    MAX_GET_LIMIT,
    CollectionNames,
    SortDirection,
)
from golf_api.models.user import User
from golf_api.permissions import UserPermissions
from golf_api.security.permissions import require_scoped_permission
from golf_api.utils.firestore import FirestoreDB
from golf_api.utils.firestore_pagination import Page, paginate_next_async

router = APIRouter(tags=['users'])


class SortField(StrEnum):
    USERID = 'userid'
    EMAIL = 'email'
    NAME = 'name'


@router.get('/', response_description='List all users')
async def list_users(
    db: FirestoreDB,  # type: ignore[valid-type]
    limit: int = Query(
        DEFAULT_GET_LIMIT,
        ge=1,
        le=MAX_GET_LIMIT,
        description='Number of users to return',
    ),
    sort_by: SortField = Query(
        SortField.USERID,
        description='Field to sort by (userid, email, name)',
    ),
    sort_direction: SortDirection = Query(
        SortDirection.ASC,
        description='Sort direction (asc, desc)',
    ),
    next_cursor: str | None = Query(
        None,
        description='Cursor for pagination (from previous response)',
    ),
    _=Depends(require_scoped_permission(UserPermissions.READ)),
) -> Page[User]:
    """List all users."""
    return await paginate_next_async(
        db=db,
        # pyrefly: ignore [bad-argument-type]
        query=db.collection(CollectionNames.USERS),
        order_by=[
            (sort_by.value, sort_direction.value),
            (FieldPath.document_id(), SortDirection.ASC),
        ],
        page_size=limit,
        model=User,
        cursor=next_cursor,
    )


@router.get('/current', response_description='Get current user')
async def get_current_user(
    user: User = Depends(require_scoped_permission(UserPermissions.READ)),
) -> User:
    return user
