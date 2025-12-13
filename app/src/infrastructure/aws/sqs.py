import boto3
from app.src.domain.jobs.queue import JobQueue
from app.src.config import Settings

class SQSJobQueue(JobQueue):
    def __init__(self, settings: Settings):
        self.queue_name = settings.queue_name
        self.sqs = boto3.client(
            "sqs",
            endpoint_url=settings.aws_endpoint_url,
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        # Cache queue URL? Or get it every time?
        # For LocalStack, getting it every time is safer as per doc, but caching is better for perf.
        # I'll get it lazily.
        self._queue_url = None

    @property
    def queue_url(self):
        if self._queue_url is None:
            response = self.sqs.get_queue_url(QueueName=self.queue_name)
            self._queue_url = response['QueueUrl']
        return self._queue_url

    def send_message(self, message_body: str) -> None:
        self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_body
        )
