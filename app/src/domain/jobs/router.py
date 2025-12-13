from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.domain.jobs.schemas import JobRequest, JobResponse, Job
from src.domain.jobs.services import JobService
from src.dependencies import get_job_service
from src.shared.result import Success, Failure

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse)
def create_job(
    request: JobRequest,
    service: Annotated[JobService, Depends(get_job_service)]
):
    result = service.create_job(request)
    match result:
        case Success(value=job):
            return job
        case Failure(error=e):
            raise HTTPException(status_code=500, detail=str(e))
        case _:
            raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    service: Annotated[JobService, Depends(get_job_service)]
):
    result = service.get_job(job_id)
    match result:
        case Success(value=job):
            return job
        case Failure(error=msg):
            raise HTTPException(status_code=404, detail=msg)
        case _:
            raise HTTPException(status_code=500, detail="Internal Server Error")
