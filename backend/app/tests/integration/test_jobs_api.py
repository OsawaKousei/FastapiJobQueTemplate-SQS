import pytest
from httpx import ASGITransport, AsyncClient

from common.config import get_settings
from common.infrastructure.aws.dynamodb import DynamoDBJobRepository
from common.jobs.schemas import Job, JobStatus
from common.jobs.services import JobService
from src.dependencies import get_job_service
from src.main import app
from tests.fakes.fake_job_queue import FakeJobQueue


@pytest.fixture
def override_dependencies():
    settings = get_settings()
    # Use real repository (connected to local DynamoDB via conftest setup)
    real_repo = DynamoDBJobRepository(settings)
    # Use Fake Queue instead of Mock
    fake_queue = FakeJobQueue()

    def get_service_override():
        return JobService(real_repo, fake_queue)

    app.dependency_overrides[get_job_service] = get_service_override
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_create_job(override_dependencies):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/jobs", json={"payload": "api_payload"})

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"

    # Verify it's in DB
    settings = get_settings()
    repo = DynamoDBJobRepository(settings)
    job = repo.get(data["job_id"])
    assert job is not None
    assert job.payload == "api_payload"


@pytest.mark.asyncio
async def test_get_job(override_dependencies):
    # First create a job directly in DB
    settings = get_settings()
    repo = DynamoDBJobRepository(settings)

    job = Job(job_id="api_job_1", status=JobStatus.COMPLETED, payload="p", result="r")
    repo.save(job)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/jobs/api_job_1")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "api_job_1"
    assert data["status"] == "COMPLETED"
    assert data["result"] == "r"


@pytest.mark.asyncio
async def test_get_job_not_found(override_dependencies):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/jobs/non_existent_api")
    assert response.status_code == 404
