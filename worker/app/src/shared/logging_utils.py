import contextvars
import logging
import uuid

# ContextVar to store request ID globally for the current context
request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="system"
)


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects the current request ID into the log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


def generate_request_id() -> str:
    """Generates a unique request ID (UUID4)."""
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    """Sets the request ID for the current context."""
    request_id_context.set(request_id)
