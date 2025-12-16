from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from common.jobs.services import JobService
from common.jobs.schemas import JobRequest, JobType, JobResponse
from common.shared.result import Success, Failure
from src.dependencies import get_job_service
from src.domain.api_b.schemas import CreateJobBRequest

router = APIRouter()

@router.post("", response_model=JobResponse)
async def create_job_b(
    request: CreateJobBRequest,
    service: Annotated[JobService, Depends(get_job_service)]
):
    job_request = JobRequest(
        job_type=JobType.JOB_B,
        payload=request.payload.model_dump()
    )
    result = service.create_job(job_request)
    
    match result:
        case Success(job):
            return job
        case Failure(error):
            raise HTTPException(status_code=500, detail=str(error))
