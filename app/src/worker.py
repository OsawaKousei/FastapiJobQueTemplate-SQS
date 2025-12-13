from typing import Any, Dict
from app.src.config import Settings
from app.src.infrastructure.aws.dynamodb import DynamoDBJobRepository
from app.src.infrastructure.aws.sqs import SQSJobQueue
from app.src.domain.jobs.services import JobService

# Initialize dependencies globally for Lambda container reuse
settings = Settings()
repository = DynamoDBJobRepository(settings)
queue = SQSJobQueue(settings) # Not strictly needed for worker unless it sends messages, but good for completeness
service = JobService(repository, queue)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SQS Trigger Handler
    """
    print("--- Lambda Worker Triggered ---")
    
    for record in event.get('Records', []):
        job_id = record.get('body')
        if not job_id:
            continue
            
        try:
            service.process_job(job_id)
        except Exception as e:
            print(f"Error processing {job_id}: {e}")
            # Raise exception to trigger SQS retry
            raise e
            
    return {"status": "success"}
