from polyfactory.factories.pydantic_factory import ModelFactory

from common.jobs.schemas import Job, JobType
from src.dispatcher import JobDispatcher
from tests.fakes.fake_services import FakeJobAService, FakeJobBService, FakeJobCService


class JobFactory(ModelFactory[Job]):
    __model__ = Job


def test_dispatch_job_a():
    # Arrange
    fake_service_a = FakeJobAService()
    fake_service_b = FakeJobBService()
    fake_service_c = FakeJobCService()
    dispatcher = JobDispatcher(fake_service_a, fake_service_b, fake_service_c)

    payload = {"message": "hello"}
    job = JobFactory.build(job_type=JobType.JOB_A, payload=payload)

    # Act
    result = dispatcher(job)

    # Assert
    assert len(fake_service_a.processed_payloads) == 1
    assert fake_service_a.processed_payloads[0].message == "hello"
    assert result["message"] == "Fake processed: hello"


def test_dispatch_job_b():
    # Arrange
    fake_service_a = FakeJobAService()
    fake_service_b = FakeJobBService()
    fake_service_c = FakeJobCService()
    dispatcher = JobDispatcher(fake_service_a, fake_service_b, fake_service_c)

    payload = {"count": 10}
    job = JobFactory.build(job_type=JobType.JOB_B, payload=payload)

    # Act
    result = dispatcher(job)

    # Assert
    assert len(fake_service_b.processed_payloads) == 1
    assert fake_service_b.processed_payloads[0].count == 10
    assert result["count_squared"] == 20  # Fake logic


def test_dispatch_job_c():
    # Arrange
    fake_service_a = FakeJobAService()
    fake_service_b = FakeJobBService()
    fake_service_c = FakeJobCService()
    dispatcher = JobDispatcher(fake_service_a, fake_service_b, fake_service_c)

    tags = ["tag1", "tag2"]
    payload = {"tags": tags}
    job = JobFactory.build(job_type=JobType.JOB_C, payload=payload)

    # Act
    result = dispatcher(job)

    # Assert
    assert len(fake_service_c.processed_payloads) == 1
    assert fake_service_c.processed_payloads[0].tags == tags
    assert result["tag_count"] == 999  # Fake logic
