import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from common.domain.job_a.job_schemas import JobAPayload
from common.jobs.schemas import JobRequest, JobType
from common.jobs.services import JobService
from common.shared.result import Failure, Success
from src.dependencies import get_job_service
from src.domain.api_a.schemas import MessageRequest, MessageResponse

router = APIRouter()


@router.post("", response_model=MessageResponse)
async def submit_message(
    request: MessageRequest, service: Annotated[JobService, Depends(get_job_service)]
) -> MessageResponse:
    # Create Job Payload
    payload = JobAPayload(message=request.text)

    # Create Job Request
    job_request = JobRequest(
        job_type=JobType.JOB_A, payload=payload.model_dump()
    )

    # Submit Job
    result = service.create_job(job_request)

    match result:
        case Success(job):
            return MessageResponse(
                request_id=str(uuid.uuid4()),
                job_id=job.job_id,
                status=job.status.value,
                text=request.text,
                processed_message=None,
            )
        case Failure(error):
            raise HTTPException(status_code=500, detail=str(error))


@router.get("/{job_id}", response_model=MessageResponse)
async def get_message_status(
    job_id: str, service: Annotated[JobService, Depends(get_job_service)]
) -> MessageResponse:
    result = service.get_job(job_id)

    match result:
        case Success(job):
            # Extract result if available
            processed_message = None
            if job.result and isinstance(job.result, dict):
                processed_message = job.result.get("message")

            # Reconstruct original text from payload if possible
            original_text = job.payload.get("message", "")

            return MessageResponse(
                request_id=str(uuid.uuid4()),  # New request ID for the query
                job_id=job.job_id,
                status=job.status.value,
                text=original_text,
                processed_message=processed_message,
            )
        case Failure(error):
            raise HTTPException(status_code=404, detail=error)
