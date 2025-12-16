from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from common.domain.job_c.job_schemas import JobCPayload
from common.jobs.schemas import JobRequest, JobType
from common.jobs.services import JobService
from common.shared.logging_utils import request_id_context
from common.shared.result import Failure, Success
from src.dependencies import get_job_service
from src.domain.api_c.schemas import TaggingRequest, TaggingResponse

router = APIRouter()


@router.post("", response_model=TaggingResponse)
async def submit_tags(
    request: TaggingRequest, service: Annotated[JobService, Depends(get_job_service)]
) -> TaggingResponse:
    # Parse tags
    tags_list = [tag.strip() for tag in request.raw_tags.split(",") if tag.strip()]

    # Create Job Payload
    payload = JobCPayload(tags=tags_list)

    # Create Job Request
    job_request = JobRequest(job_type=JobType.JOB_C, payload=payload.model_dump())

    # Submit Job
    result = service.create_job(job_request)

    match result:
        case Success(job):
            return TaggingResponse(
                request_id=request_id_context.get(),
                job_id=job.job_id,
                status=job.status.value,
                tag_count=None,
                tags=None,
            )
        case Failure(error):
            raise HTTPException(status_code=500, detail=str(error))


@router.get("/{job_id}", response_model=TaggingResponse)
async def get_tagging_status(
    job_id: str, service: Annotated[JobService, Depends(get_job_service)]
) -> TaggingResponse:
    result = service.get_job(job_id)

    match result:
        case Success(job):
            # Extract result if available
            tag_count = None
            tags = None
            if job.result and isinstance(job.result, dict):
                tag_count = job.result.get("tag_count")
                tags = job.result.get("tags")

            return TaggingResponse(
                request_id=request_id_context.get(),
                job_id=job.job_id,
                status=job.status.value,
                tag_count=tag_count,
                tags=tags,
            )
        case Failure(error):
            raise HTTPException(status_code=404, detail=error)
