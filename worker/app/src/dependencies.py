from src.config import get_settings
from src.domain.jobs.services import JobService
from src.infrastructure.aws.dynamodb import DynamoDBJobRepository
from src.infrastructure.aws.sqs import SQSJobQueue


def get_job_service() -> JobService:
    settings = get_settings()
    repository = DynamoDBJobRepository(settings)
    queue = SQSJobQueue(settings)
    return JobService(repository, queue)
