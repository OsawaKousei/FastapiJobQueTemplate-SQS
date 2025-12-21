from common.jobs.queue import JobQueue, QueueMessage


class FakeJobQueue(JobQueue):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, message_body: str) -> None:
        self.messages.append(message_body)

    def receive_messages(
        self, max_messages: int = 1, wait_time_seconds: int = 20
    ) -> list[QueueMessage]:
        # Not implemented for now as we only test sending in the service test
        return []

    def delete_message(self, receipt_handle: str) -> None:
        pass
