from polyfactory.factories.pydantic_factory import ModelFactory

from common.domain.job_a.job_schemas import JobAPayload, JobAResult
from src.domain.job_a.service import JobAService


class JobAPayloadFactory(ModelFactory[JobAPayload]):
    __model__ = JobAPayload


def test_process_returns_success_result():
    # Arrange
    payload = JobAPayloadFactory.build()
    service = JobAService()

    # Act
    result = service.process(payload)

    # Assert
    assert isinstance(result, JobAResult)
    assert result.status == "success"
    assert result.message == f"Processed Job A: {payload.message}"
