import boto3

from common.config import Settings
from common.modules.queue import JobQueue, QueueMessage


class SQSJobQueue(JobQueue):
    def __init__(self, settings: Settings) -> None:
        self.queue_name = settings.queue_name
        self.sqs = boto3.client(
            "sqs",
            endpoint_url=settings.aws_endpoint_url,
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        # Cache queue URL? Or get it every time?
        # For LocalStack, getting it every time is safer as per doc,
        # but caching is better for perf.
        # I'll get it lazily.
        self._queue_url = None

    @property
    def queue_url(self) -> str:
        if self._queue_url is None:
            response = self.sqs.get_queue_url(QueueName=self.queue_name)
            self._queue_url = response["QueueUrl"]
        return self._queue_url

    def send_message(self, message_body: str) -> None:
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=message_body)

    def receive_messages(
        self, max_messages: int = 1, wait_time_seconds: int = 20
    ) -> list[QueueMessage]:
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds,
        )
        messages = []
        if "Messages" in response:
            for msg in response["Messages"]:
                messages.append(
                    QueueMessage(
                        message_id=msg["MessageId"],
                        body=msg["Body"],
                        receipt_handle=msg["ReceiptHandle"],
                    )
                )
        return messages

    def delete_message(self, receipt_handle: str) -> None:
        self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
