"""Verifies the bearer token in the Authorization header."""

import asyncio
from functools import lru_cache
import logging

import cachecontrol
from fastapi import HTTPException, status
from google.auth import exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
import requests

from golf_api.models.user import User
from golf_api.settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_google_request():
    session = requests.Session()
    cached_session = cachecontrol.CacheControl(session)
    return google_requests.Request(session=cached_session)


async def verify_bearer_token(token: str) -> User:
    try:
        request = get_google_request()
        payload = await asyncio.to_thread(
            google_id_token.verify_oauth2_token,
            token,
            request=request,
            audience=settings.client_id,
        )
    except exceptions.GoogleAuthError as e:
        logger.error('Invalid issuer in Google ID token: %s', e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid issuer'
        ) from e
    except ValueError as e:
        logger.info('Bearer token verification failed: %s', e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token'
        ) from e

    userid = payload.get('sub')
    email = payload.get('email')

    if not userid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token payload',
        )

    return User(
        userid=userid,
        email=email,
        name=payload.get('name'),
    )
