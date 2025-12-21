from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from common.config import Settings, get_settings
from common.infrastructure.aws.dynamodb import DynamoDBJobRepository
from common.infrastructure.aws.sqs import SQSJobQueue
from common.jobs.processor import JobProcessor
from src.dispatcher import JobDispatcher
from src.domain.job_a.service import JobAService
from src.domain.job_b.service import JobBService
from src.domain.job_c.service import JobCService


@lru_cache
def get_app_settings() -> Settings:
    return get_settings()


def get_job_repository(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> DynamoDBJobRepository:
    return DynamoDBJobRepository(settings)


def get_job_queue(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SQSJobQueue:
    return SQSJobQueue(settings)


def get_job_dispatcher() -> JobDispatcher:
    service_a = JobAService()
    service_b = JobBService()
    service_c = JobCService()
    return JobDispatcher(service_a, service_b, service_c)


def get_job_processor(
    repository: Annotated[DynamoDBJobRepository, Depends(get_job_repository)],
    queue: Annotated[SQSJobQueue, Depends(get_job_queue)],
    dispatcher: Annotated[JobDispatcher, Depends(get_job_dispatcher)],
) -> JobProcessor:
    return JobProcessor(repository, queue, dispatcher)
