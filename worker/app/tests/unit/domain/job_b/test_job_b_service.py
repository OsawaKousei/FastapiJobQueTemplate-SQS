from polyfactory.factories.pydantic_factory import ModelFactory

from common.domain.job_b.job_schemas import JobBPayload, JobBResult
from src.domain.job_b.service import JobBService


class JobBPayloadFactory(ModelFactory[JobBPayload]):
    __model__ = JobBPayload


def test_process_returns_squared_count():
    # Arrange
    payload = JobBPayloadFactory.build(count=5)
    service = JobBService()

    # Act
    result = service.process(payload)

    # Assert
    assert isinstance(result, JobBResult)
    assert result.status == "success"
    assert result.count_squared == 25
