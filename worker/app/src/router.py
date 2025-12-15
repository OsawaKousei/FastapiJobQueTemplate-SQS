import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends

from common.jobs.processor import JobProcessor
from src.dependencies import get_job_processor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def handle_sqs_event(
    event: Dict[str, Any],
    processor: Annotated[JobProcessor, Depends(get_job_processor)],
) -> Dict[str, Any]:
    """
    Handle SQS events triggered via Lambda Adapter or similar.
    """
    logger.info(f"Received event: {event}")

    # Check if it's an SQS event
    records = event.get("Records", [])
    if not records:
        logger.warning("No records found in event")
        return {"status": "no_records"}

    processed_count = 0
    failed_count = 0

    for record in records:
        try:
            # SQS body is the job_id
            job_id = record.get("body")
            if not job_id:
                logger.warning(f"Record has no body: {record}")
                continue

            # Process the job
            processor.process_job(job_id)
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to process record: {e}")
            failed_count += 1

    return {
        "status": "processed",
        "processed_count": processed_count,
        "failed_count": failed_count,
    }
