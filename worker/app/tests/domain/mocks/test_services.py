import pytest

from src.domain.mocks.exceptions import MockAlreadyExistsError, MockNotFoundError
from src.domain.mocks.schemas import (
    HttpMethod,
    MockCreate,
    MockEndpoint,
)
from src.domain.mocks.services import MockManagementService, MockSimulatorService
from src.domain.mocks.template_engine import TemplateEngine
from src.shared.result import Failure, Success


class InMemoryMockRepository:
    def __init__(self):
        self.store: dict[str, MockEndpoint] = {}  # id -> mock
        self.lookup: dict[str, str] = {}  # method:path -> id

    async def save(self, mock: MockEndpoint) -> None:
        self.store[mock.id] = mock
        self.lookup[mock.key] = mock.id

    async def find(self, method: HttpMethod, path: str) -> MockEndpoint | None:
        key = f"{method}:{path}"
        mock_id = self.lookup.get(key)
        if mock_id:
            return self.store.get(mock_id)
        return None

    async def delete(self, mock_id: str) -> bool:
        if mock_id in self.store:
            mock = self.store[mock_id]
            del self.store[mock_id]
            del self.lookup[mock.key]
            return True
        return False

    async def find_by_id(self, mock_id: str) -> MockEndpoint | None:
        return self.store.get(mock_id)

    async def find_all(self) -> list[MockEndpoint]:
        return list(self.store.values())


@pytest.mark.asyncio
class TestMockManagementService:
    async def test_register_success(self):
        repo = InMemoryMockRepository()
        service = MockManagementService(repo)

        create_dto = MockCreate(
            path="/test",
            method=HttpMethod.GET,
            status_code=200,
            response_body={"msg": "hello"},
        )

        result = await service.register(create_dto)

        assert isinstance(result, Success)
        assert result.value.path == "/test"
        assert result.value.id is not None

        # Verify repo
        saved = await repo.find(HttpMethod.GET, "/test")
        assert saved is not None
        assert saved.id == result.value.id

    async def test_register_duplicate(self):
        repo = InMemoryMockRepository()
        service = MockManagementService(repo)

        create_dto = MockCreate(path="/test", method=HttpMethod.GET, status_code=200)

        await service.register(create_dto)
        result = await service.register(create_dto)

        assert isinstance(result, Failure)
        assert isinstance(result.error, MockAlreadyExistsError)

    async def test_delete_success(self):
        repo = InMemoryMockRepository()
        service = MockManagementService(repo)

        create_dto = MockCreate(path="/test", method=HttpMethod.GET)
        created = (await service.register(create_dto)).value

        result = await service.delete(created.id)

        assert isinstance(result, Success)
        assert result.value is True
        assert await repo.find(HttpMethod.GET, "/test") is None

    async def test_delete_not_found(self):
        repo = InMemoryMockRepository()
        service = MockManagementService(repo)

        result = await service.delete("non-existent")

        assert isinstance(result, Failure)
        assert isinstance(result.error, MockNotFoundError)


@pytest.mark.asyncio
class TestMockSimulatorService:
    async def test_execute_success(self):
        repo = InMemoryMockRepository()
        template_engine = TemplateEngine()
        service = MockSimulatorService(repo, template_engine)

        # Setup mock
        mock = MockEndpoint(
            id="1",
            path="/test",
            method=HttpMethod.GET,
            status_code=201,
            response_body={"id": "{{uuid}}"},
            headers={"X-Test": "1"},
        )
        await repo.save(mock)

        result = await service.execute("GET", "/test")

        assert isinstance(result, Success)
        sim_result = result.value
        assert sim_result.status_code == 201
        assert sim_result.headers["X-Test"] == "1"
        assert isinstance(sim_result.body, dict)
        assert len(sim_result.body["id"]) == 36  # UUID length

    async def test_execute_not_found(self):
        repo = InMemoryMockRepository()
        template_engine = TemplateEngine()
        service = MockSimulatorService(repo, template_engine)

        result = await service.execute("GET", "/not-found")

        assert isinstance(result, Failure)
        assert isinstance(result.error, MockNotFoundError)
