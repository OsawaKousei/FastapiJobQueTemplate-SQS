from typing import Protocol

class JobQueue(Protocol):
    def send_message(self, message_body: str) -> None:
        ...
