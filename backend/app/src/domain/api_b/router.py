from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from common.domain.job_b.job_schemas import JobBPayload
from common.jobs.schemas import JobRequest, JobType
from common.jobs.services import JobService
from common.shared.logging_utils import request_id_context
from common.shared.result import Failure, Success
from src.dependencies import get_job_service
from src.domain.api_b.schemas import GenerateSequenceRequest, SequenceResponse

router = APIRouter()


@router.post("", response_model=SequenceResponse)
async def generate_sequence(
    request: GenerateSequenceRequest,
    service: Annotated[JobService, Depends(get_job_service)],
) -> SequenceResponse:
    # Create Job Payload
    payload = JobBPayload(count=request.length)

    # Create Job Request
    job_request = JobRequest(job_type=JobType.JOB_B, payload=payload.model_dump())

    # Submit Job
    result = service.create_job(job_request)

    match result:
        case Success(job):
            return SequenceResponse(
                task_id=request_id_context.get(),
                job_id=job.job_id,
                status=job.status.value,
                squared_result=None,
            )
        case Failure(error):
            raise HTTPException(status_code=500, detail=str(error))


@router.get("/{job_id}", response_model=SequenceResponse)
async def get_sequence_status(
    job_id: str, service: Annotated[JobService, Depends(get_job_service)]
) -> SequenceResponse:
    result = service.get_job(job_id)

    match result:
        case Success(job):
            # Extract result if available
            squared_result = None
            if job.result and isinstance(job.result, dict):
                squared_result = job.result.get("count_squared")

            return SequenceResponse(
                task_id=request_id_context.get(),
                job_id=job.job_id,
                status=job.status.value,
                squared_result=squared_result,
            )
        case Failure(error):
            raise HTTPException(status_code=404, detail=error)
