"""Firestore utility functions."""

from typing import Annotated

from fastapi import Depends, Request
from google.cloud import firestore


def get_firestore(request: Request) -> firestore.AsyncClient:
    """
    Get the Firestore client from the application state.

    This is used as a FastAPI dependency to inject the Firestore client
    into route handlers.

    Args:
        request: The FastAPI request object

    Returns:
        The Firestore AsyncClient instance
    """
    return request.app.state.db_client


FirestoreDB = Annotated[firestore.AsyncClient, Depends(get_firestore)]
