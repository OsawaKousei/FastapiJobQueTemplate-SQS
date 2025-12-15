import logging
import time
from typing import Any, Dict

from common.config import get_settings
from common.infrastructure.aws.dynamodb import DynamoDBJobRepository
from common.jobs.schemas import JobStatus

logger = logging.getLogger(__name__)

# Initialize repository globally for Lambda container reuse
settings = get_settings()
repository = DynamoDBJobRepository(settings)


def job_handler(payload: str) -> str:
    """
    Actual job processing logic.
    """
    logger.info(f"[Worker] Processing payload: {payload}")

    # Simulate heavy computation
    time.sleep(3)

    result = f"Processed: {payload}"
    logger.info(f"[Worker] Finished processing: {result}")
    return result


def process_single_job(job_id: str) -> None:
    """
    Process a single job by ID.
    """
    logger.info(f"Processing job: {job_id}")

    # 1. Update status to PROCESSING
    repository.update_status(job_id, JobStatus.PROCESSING)

    try:
        # 2. Get job details
        job = repository.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in repository")
            return

        # 3. Run handler
        result_data = job_handler(job.payload)

        # 4. Update status to COMPLETED
        repository.update_status(job_id, JobStatus.COMPLETED, result_data)

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        # Optionally update status to FAILED
        # repository.update_status(job_id, JobStatus.FAILED, str(e))
        raise e


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SQS Trigger Handler (Lambda style)
    """
    logger.info("--- Lambda Worker Triggered ---")

    for record in event.get("Records", []):
        # SQS event body is the job_id (as per previous logic)
        job_id = record.get("body")
        if not job_id:
            continue

        try:
            process_single_job(job_id)
        except Exception as e:
            logger.error(f"Error processing {job_id}: {e}")
            # Raise exception to trigger SQS retry (if configured)
            raise e

    return {"status": "success"}
