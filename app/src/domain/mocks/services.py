import asyncio
import json
import uuid
from datetime import datetime, timezone

from src.domain.mocks.exceptions import MockAlreadyExistsError, MockNotFoundError
from src.domain.mocks.repository import MockRepository
from src.domain.mocks.schemas import (
    HttpMethod,
    MockCreate,
    MockEndpoint,
    MockTemplateContext,
    SimulationResult,
)
from src.domain.mocks.template_engine import TemplateEngine
from src.shared.result import Failure, Result, Success


class MockManagementService:
    def __init__(self, repo: MockRepository) -> None:
        self._repo = repo

    async def register(
        self, create_schema: MockCreate
    ) -> Result[MockEndpoint, MockAlreadyExistsError]:
        # Check if exists
        existing = await self._repo.find(create_schema.method, create_schema.path)
        if existing:
            return Failure(
                MockAlreadyExistsError(create_schema.method, create_schema.path)
            )

        # Create new entity
        new_mock = MockEndpoint(
            id=str(uuid.uuid4()),
            path=create_schema.path,
            method=create_schema.method,
            status_code=create_schema.status_code,
            response_body=create_schema.response_body,
            headers=create_schema.headers,
            latency_ms=create_schema.latency_ms,
        )

        await self._repo.save(new_mock)
        return Success(new_mock)

    async def delete(self, mock_id: str) -> Result[bool, MockNotFoundError]:
        deleted = await self._repo.delete(mock_id)
        if not deleted:
            # We don't know method/path here easily without lookup,
            # but MockNotFoundError expects them.
            # Let's try to find it first? Or change MockNotFoundError?
            # For now, let's assume delete returns False if not found.
            return Failure(
                MockNotFoundError(
                    method="?", path="?", message=f"Mock {mock_id} not found"
                )
            )
        return Success(True)

    async def get_all(self) -> Result[list[MockEndpoint], Exception]:
        mocks = await self._repo.find_all()
        return Success(mocks)


class MockSimulatorService:
    def __init__(self, repo: MockRepository, template_engine: TemplateEngine) -> None:
        self._repo = repo
        self._template_engine = template_engine

    async def execute(
        self, method: str, path: str
    ) -> Result[SimulationResult, MockNotFoundError]:
        # 1. Lookup
        # method string to Enum
        try:
            http_method = HttpMethod(method.upper())
        except ValueError:
            return Failure(MockNotFoundError(method, path, "Invalid HTTP Method"))

        mock = await self._repo.find(http_method, path)
        if not mock:
            return Failure(MockNotFoundError(method, path))

        # 2. Latency Simulation
        if mock.latency_ms > 0:
            await asyncio.sleep(mock.latency_ms / 1000)

        # 3. Template Processing
        # Prepare context
        context = MockTemplateContext(
            request_id=str(uuid.uuid4()),  # Or get from contextvar if needed
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Handle body (dict or str)
        final_body: str | dict
        if isinstance(mock.response_body, dict):
            # Convert to str, render, convert back
            body_str = json.dumps(mock.response_body)
            rendered_str = self._template_engine.render(body_str, context)
            try:
                final_body = json.loads(rendered_str)
            except json.JSONDecodeError:
                # Fallback to string if invalid JSON after render
                final_body = rendered_str
        else:
            final_body = self._template_engine.render(mock.response_body, context)

        # 4. Return Result
        return Success(
            SimulationResult(
                status_code=mock.status_code, body=final_body, headers=mock.headers
            )
        )
