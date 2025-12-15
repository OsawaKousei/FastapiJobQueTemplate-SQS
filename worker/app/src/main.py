import logging
import logging.config
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

import yaml
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict

from common.shared.logging_utils import generate_request_id, set_request_id
from src.router import router as worker_router

# Load logging configuration
try:
    with open("src/logging_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)
except FileNotFoundError:
    logging.basicConfig(level=logging.INFO)
    logging.warning("logging_config.yaml not found, using basic config.")

logger = logging.getLogger("app")


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: str
    message: str


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Worker application startup.")
    yield
    logger.info("Worker application shutdown.")


app = FastAPI(
    title="Worker Service",
    description="Worker service for processing jobs.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID") or generate_request_id()
    set_request_id(request_id)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="Worker is running.")


app.include_router(worker_router)
