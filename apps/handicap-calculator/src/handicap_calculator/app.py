"""Entrypoint for the API application."""

import logging

from fastapi import FastAPI

from handicap_calculator.routes import health

logger = logging.getLogger(__name__)


app = FastAPI()

app.include_router(health.router, prefix='/health')
