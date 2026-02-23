"""Entrypoint for the API application."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore

from golf_api.routes import health, users
from golf_api.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Lifespan context manager for the application."""
    # Initialize Firestore client
    client_kwargs = {}

    # Set project ID if provided
    if settings.firestore_project_id:
        client_kwargs['project'] = settings.firestore_project_id

    # Use Firestore emulator if configured
    if settings.firestore_emulator_host:
        logger.info(
            'Using Firestore emulator at %s', settings.firestore_emulator_host
        )
        # Use client_options to connect to the emulator, avoiding os.environ
        client_kwargs['client_options'] = {
            'api_endpoint': settings.firestore_emulator_host
        }
        # Emulator requires a project ID, use a dummy one if not provided
        if 'project' not in client_kwargs:
            client_kwargs['project'] = 'emulator-project'

    application.state.db_client = firestore.AsyncClient(**client_kwargs)
    logger.info('Firestore client initialized')

    yield

    # Cleanup
    application.state.db_client.close()
    logger.info('Firestore client closed')


app = FastAPI(lifespan=lifespan)

# Configure CORS
if settings.client_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.client_origins,
        allow_credentials=False,
        allow_methods=['GET', 'POST'],
        allow_headers=['Content-Type', 'Authorization'],
    )

app.include_router(health.router, prefix='/health')
app.include_router(users.router, prefix='/api/v1/users')
