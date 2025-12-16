import logging
from typing import Protocol, Any, Dict

from common.jobs.queue import JobQueue
from common.jobs.repository import JobRepository
from common.jobs.schemas import JobStatus, Job

logger = logging.getLogger(__name__)


class JobDispatcher(Protocol):
    def __call__(self, job: Job) -> Dict[str, Any]: ...


class JobProcessor:
    def __init__(
        self,
        repository: JobRepository,
        queue: JobQueue,
        dispatcher: JobDispatcher,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.dispatcher = dispatcher

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

        try:
            self.process_job(job_id)
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")

        # Delete message from queue after processing attempt
        self.queue.delete_message(message.receipt_handle)
        return True

    def process_job(self, job_id: str) -> None:
        """
        Process a single job by ID.
        """
        logger.info(f"Processing job: {job_id}")

        # Update status to PROCESSING
        self.repository.update_status(job_id, JobStatus.PROCESSING)

        try:
            # Get job details to get payload
            job = self.repository.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found in repository")
                return

            # Run dispatcher
            result = self.dispatcher(job)

            # Update status to COMPLETED
            self.repository.update_status(job_id, JobStatus.COMPLETED, result)
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self.repository.update_status(job_id, JobStatus.FAILED, str(e))
            raise e
