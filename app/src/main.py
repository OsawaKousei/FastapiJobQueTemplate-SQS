import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, Awaitable, Callable

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from src.dependencies import get_mock_sim_service
from src.domain.mocks.exceptions import MockNotFoundError
from src.domain.mocks.router import router as mocks_router
from src.domain.mocks.services import MockSimulatorService
from src.shared.logging_utils import generate_request_id, set_request_id
from src.shared.result import Failure, Success

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
    title="Serverless Mock API Generator",
    description="A serverless API to manage and simulate mock endpoints.",
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
app.include_router(mocks_router)


# 7. Simulation Catch-all Route
async def _execute_simulation(
    request: Request,
    path: str,
    service: MockSimulatorService,
) -> Response:
    # 1. Construct search key
    # FastAPI strips the leading slash from path parameter
    full_path = f"/{path}"
    method = request.method

    # 2. Execute simulation
    result = await service.execute(method, full_path)

    # 3. Build response
    match result:
        case Success(sim_result):
            # If body is string, we might want to return Response directly
            # to avoid extra quoting
            if isinstance(sim_result.body, str):
                return Response(
                    content=sim_result.body,
                    status_code=sim_result.status_code,
                    headers=sim_result.headers,
                )

            return JSONResponse(
                content=sim_result.body,
                status_code=sim_result.status_code,
                headers=sim_result.headers,
            )
        case Failure(MockNotFoundError()):
            raise HTTPException(status_code=404, detail="Mock not found")
        case Failure(e):
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/{path:path}")
async def simulate_get(
    request: Request,
    path: str,
    service: Annotated[MockSimulatorService, Depends(get_mock_sim_service)],
) -> Response:
    return await _execute_simulation(request, path, service)


@app.api_route("/{path:path}", methods=["POST", "PUT", "DELETE", "PATCH"])
async def simulate_others(
    request: Request,
    path: str,
    service: Annotated[MockSimulatorService, Depends(get_mock_sim_service)],
) -> Response:
    return await _execute_simulation(request, path, service)
