import logging
import logging.config
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

import yaml
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict

from common.shared.logging_utils import generate_request_id, set_request_id
from src.domain.api_a.router import router as api_a_router
from src.domain.api_b.router import router as api_b_router
from src.domain.api_c.router import router as api_c_router

# Load logging configuration
try:
    with open("src/logging_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)
except FileNotFoundError:
    logging.basicConfig(level=logging.INFO)
    logging.warning("logging_config.yaml not found, using basic config.")

logger = logging.getLogger("app")


# 1. Schema Definition (Minimal Strict Guideline Compliance)
class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: str
    message: str


# 2. Lifespan Management
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup logic
    logger.info("Application startup sequence initiated.")

    yield

    # Shutdown logic
    logger.info("Application shutdown sequence initiated.")


# 3. App Definition
app = FastAPI(
    title="Serverless Job Queue API",
    description="A serverless API to manage jobs using SQS and Lambda.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# 4. Middleware
@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID") or generate_request_id()
    set_request_id(request_id)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response


# 5. Root Endpoint (Health Check)
@app.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    logger.info("Health check endpoint called.")
    return HealthResponse(
        status="ok",
        message="Server is running.",
    )


# 6. Router Registration
app.include_router(jobs_router)
app.include_router(api_b_router, prefix="/jobs/b", tags=["job_b"])
app.include_router(api_c_router, prefix="/jobs/c", tags=["job_c"])

