from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class QueueMessage:
    message_id: str
    body: str
    receipt_handle: str


class JobQueue(Protocol):
    def send_message(self, message_body: str) -> None: ...

    def receive_messages(
        self, max_messages: int = 1, wait_time_seconds: int = 20
    ) -> list[QueueMessage]: ...

    def delete_message(self, receipt_handle: str) -> None: ...
