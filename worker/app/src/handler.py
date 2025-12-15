import logging
import time

logger = logging.getLogger(__name__)


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
