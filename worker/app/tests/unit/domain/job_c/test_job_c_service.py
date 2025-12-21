from polyfactory.factories.pydantic_factory import ModelFactory

from common.domain.job_c.job_schemas import JobCPayload, JobCResult
from src.domain.job_c.service import JobCService


class JobCPayloadFactory(ModelFactory[JobCPayload]):
    __model__ = JobCPayload


def test_process_returns_tag_count():
    # Arrange
    tags = ["tag1", "tag2", "tag3"]
    payload = JobCPayloadFactory.build(tags=tags)
    service = JobCService()

    # Act
    result = service.process(payload)

    # Assert
    assert isinstance(result, JobCResult)
    assert result.status == "success"
    assert result.tag_count == 3
    assert result.tags == tags
