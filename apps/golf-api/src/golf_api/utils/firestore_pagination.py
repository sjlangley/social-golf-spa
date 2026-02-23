import base64
from datetime import datetime, timezone
import json
from typing import Generic, Type, TypeVar

from google.cloud import firestore
from pydantic import BaseModel, Field

from golf_api.constants import MAX_GET_LIMIT

T = TypeVar('T', bound=BaseModel)


class Page(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    next_cursor: str | None = None


def _json_default(obj):
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=timezone.utc)
        return obj.astimezone(timezone.utc).isoformat()
    raise TypeError(f'Not JSON serializable: {type(obj)}')


def _maybe_parse_datetime(value):
    if isinstance(value, str) and 'T' in value:
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return value
    return value


def encode_cursor(values):
    raw = json.dumps(
        values, separators=(',', ':'), default=_json_default
    ).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor):
    raw = base64.urlsafe_b64decode(cursor.encode())
    values = json.loads(raw.decode())
    return {k: _maybe_parse_datetime(v) for k, v in values.items()}


async def paginate_next_async(
    *,
    db: firestore.AsyncClient,
    query: firestore.Query,
    order_by: list,
    page_size: int,
    model: Type[T],
    cursor: str | None = None,
) -> Page[T]:
    """
    Generic forward-only Firestore cursor pagination.

    Parameters:
        db: firestore.AsyncClient
        query: Firestore query (e.g. db.collection("posts"))
        order_by: list of tuples like:
            [("created_at", "desc"), ("__name__", "asc")]
            ALWAYS include "__name__" last for stable ordering.
        page_size: int (1-{MAX_GET_LIMIT} recommended)
        cursor: opaque cursor string from previous page

    Returns:
        {
            "items": [...],
            "next_cursor": "<opaque token>" | None
        }
    """

    if page_size < 1 or page_size > MAX_GET_LIMIT:
        raise ValueError(f'page_size must be between 1 and {MAX_GET_LIMIT}')

    if not order_by:
        raise ValueError('order_by must have at least one field')

    q = query

    # Apply ordering
    for field, direction in order_by:
        q = q.order_by(
            field,
            direction=(
                firestore.Query.ASCENDING
                if direction in ('asc', firestore.Query.ASCENDING)
                else firestore.Query.DESCENDING
            ),
        )

    # Apply cursor (start_after)
    if cursor:
        try:
            last_values = decode_cursor(cursor)
        except Exception as e:
            raise ValueError('Invalid cursor') from e

        cursor_values = []

        for field, _ in order_by:
            if field not in last_values:
                raise ValueError(f"Cursor missing field '{field}'")

            value = last_values[field]

            if field == '__name__':
                # convert stored document path string back to DocumentReference
                # pyrefly: ignore [bad-argument-type]
                value = db.document(value)

            cursor_values.append(value)

        q = q.start_after(cursor_values)

    items: list[T] = []
    docs_data: list[tuple] = []  # Store (doc, data) pairs

    # Fetch page_size + 1 to check if there are more items
    # pyrefly: ignore [not-iterable]
    async for doc in q.limit(page_size + 1).stream():
        data = doc.to_dict() or {}
        items.append(model.model_validate(data))
        docs_data.append((doc, data))

    # Build next cursor only if there are more items beyond the current page
    next_cursor = None
    has_more = len(items) > page_size

    if has_more:
        # Remove the extra item
        items = items[:page_size]
        # Use the last item we're returning to build the cursor
        last_doc, last_data = docs_data[page_size - 1]

        payload = {}

        for field, _ in order_by:
            if field == '__name__':
                payload['__name__'] = last_doc.reference.path
            else:
                if field not in last_data:
                    raise ValueError(
                        f"Last document missing required order field '{field}'"
                    )
                payload[field] = last_data[field]

        next_cursor = encode_cursor(payload)

    return Page[T](items=items, next_cursor=next_cursor)
