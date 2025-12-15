import logging
from typing import Protocol

from common.jobs.queue import JobQueue
from common.jobs.repository import JobRepository
from common.jobs.schemas import JobStatus

logger = logging.getLogger(__name__)


class JobHandler(Protocol):
    def __call__(self, payload: str) -> str: ...


class JobProcessor:
    def __init__(
        self,
        repository: JobRepository,
        queue: JobQueue,
        handler: JobHandler,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.handler = handler

    def process_next(self) -> bool:
        """
        Process the next message from the queue.
        Returns True if a message was processed, False otherwise.
        """
        messages = self.queue.receive_messages(max_messages=1)
        if not messages:
            return False

        message = messages[0]
        job_id = message.body  # Assuming message body is job_id

        logger.info(f"Processing job: {job_id}")

        # Update status to PROCESSING
        self.repository.update_status(job_id, JobStatus.PROCESSING)

        try:
            # Get job details to get payload
            job = self.repository.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found in repository")
                # If job is not found, we can't process it.
                # Delete message to avoid loop.
                self.queue.delete_message(message.receipt_handle)
                return True

            # Execute handler
            result = self.handler(job.payload)

            # Update status to COMPLETED
            self.repository.update_status(job_id, JobStatus.COMPLETED, result=result)
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self.repository.update_status(job_id, JobStatus.FAILED, result=str(e))
            # Depending on policy, we might not delete the message to retry,
            # or delete it to avoid infinite loop if it's a logic error.
            # For now, let's assume we delete it and handle retry elsewhere or use DLQ.

        # Delete message from queue
        self.queue.delete_message(message.receipt_handle)
        return True
