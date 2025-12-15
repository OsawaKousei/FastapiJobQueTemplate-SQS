from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from common.config import get_settings
from common.infrastructure.aws.dynamodb import DynamoDBJobRepository
from common.infrastructure.aws.sqs import SQSJobQueue
from common.jobs.services import JobService
from src.dependencies import get_job_service
from src.main import app

client = TestClient(app)

# Mock SQS because we might not have a real SQS container
# We only want to test the API -> Service -> Repository flow with real DB
# But Service also calls Queue.
# We can override the dependency to use a real Repository but a Mock Queue.


@pytest.fixture
def override_dependencies():
    settings = get_settings()
    real_repo = DynamoDBJobRepository(settings)
    mock_queue = MagicMock(spec=SQSJobQueue)

    def get_service_override():
        return JobService(real_repo, mock_queue)

    app.dependency_overrides[get_job_service] = get_service_override
    yield
    app.dependency_overrides = {}


def test_create_job(override_dependencies):
    response = client.post("/jobs", json={"payload": "api_payload"})
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


def test_get_job(override_dependencies):
    # First create a job directly in DB
    settings = get_settings()
    repo = DynamoDBJobRepository(settings)
    from common.jobs.schemas import Job, JobStatus

    job = Job(job_id="api_job_1", status=JobStatus.COMPLETED, payload="p", result="r")
    repo.save(job)

    response = client.get("/jobs/api_job_1")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "api_job_1"
    assert data["status"] == "COMPLETED"
    assert data["result"] == "r"


def test_get_job_not_found(override_dependencies):
    response = client.get("/jobs/non_existent_api")
    assert response.status_code == 404
