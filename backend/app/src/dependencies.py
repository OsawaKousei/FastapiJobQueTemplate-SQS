from common.config import get_settings
from common.infrastructure.aws.dynamodb import DynamoDBJobRepository
from common.infrastructure.aws.sqs import SQSJobQueue
from common.jobs.services import JobService


def get_job_service() -> JobService:
    settings = get_settings()
    repository = DynamoDBJobRepository(settings)
    queue = SQSJobQueue(settings)
    return JobService(repository, queue)
