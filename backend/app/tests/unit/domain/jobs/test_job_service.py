import pytest
from polyfactory.factories.pydantic_factory import ModelFactory

from common.jobs.schemas import Job, JobRequest, JobStatus
from common.jobs.services import JobService
from common.shared.result import Failure, Success
from tests.fakes.fake_job_queue import FakeJobQueue
from tests.fakes.fake_job_repo import FakeJobRepository


class JobFactory(ModelFactory[Job]):
    __model__ = Job


class JobRequestFactory(ModelFactory[JobRequest]):
    __model__ = JobRequest


@pytest.fixture
def fake_repo() -> FakeJobRepository:
    return FakeJobRepository()


@pytest.fixture
def fake_queue() -> FakeJobQueue:
    return FakeJobQueue()


@pytest.fixture
def service(fake_repo: FakeJobRepository, fake_queue: FakeJobQueue) -> JobService:
    return JobService(repository=fake_repo, queue=fake_queue)


def test_create_job_success(
    service: JobService, fake_repo: FakeJobRepository, fake_queue: FakeJobQueue
) -> None:
    # Arrange
    request = JobRequestFactory.build(payload="test_payload")

    # Act
    result = service.create_job(request)

    # Assert
    assert isinstance(result, Success)
    job = result.value
    assert job.payload == "test_payload"
    assert job.status == JobStatus.QUEUED
    assert job.job_id is not None

    # Verify side effects on Fakes
    saved_job = fake_repo.get(job.job_id)
    assert saved_job == job
    assert job.job_id in fake_queue.messages


def test_create_job_failure_repo(
    fake_repo: FakeJobRepository, fake_queue: FakeJobQueue
) -> None:
    # Arrange
    # Simulate repo failure by overriding save method on the instance or subclassing
    # Since we want to avoid mocking, we can create a BrokenFakeRepo
    class BrokenFakeRepo(FakeJobRepository):
        def save(self, job: Job) -> Job:
            raise Exception("DB Error")

    broken_repo = BrokenFakeRepo()
    service = JobService(repository=broken_repo, queue=fake_queue)
    request = JobRequestFactory.build()

    # Act
    result = service.create_job(request)

    # Assert
    assert isinstance(result, Failure)
    assert "DB Error" in str(result.error)
    assert len(fake_queue.messages) == 0


def test_get_job_found(service: JobService, fake_repo: FakeJobRepository) -> None:
    # Arrange
    job = JobFactory.build(job_id="test_id", status=JobStatus.QUEUED)
    fake_repo.save(job)

    # Act
    result = service.get_job("test_id")

    # Assert
    assert isinstance(result, Success)
    assert result.value == job


def test_get_job_not_found(service: JobService) -> None:
    # Act
    result = service.get_job("non_existent")

    # Assert
    assert isinstance(result, Failure)
    assert result.error == "Job not found"
