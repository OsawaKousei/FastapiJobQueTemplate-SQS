import time
from typing import Union

from src.domain.jobs.repository import JobRepository
from src.domain.jobs.schemas import Job, JobRequest, JobStatus
from src.shared.result import Failure, Success

Result = Union[Success[Job], Failure[Exception]]


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def get_job(self, job_id: str) -> Union[Success[Job], Failure[str]]:
        job = self.repository.get(job_id)
        if job:
            return Success(job)
        return Failure("Job not found")

    def process_job(self, job_id: str) -> None:
        print(f"[Logic] Start processing job: {job_id}")

        # 1. Update status to PROCESSING
        self.repository.update_status(job_id, JobStatus.PROCESSING)

        # Heavy computation simulation
        time.sleep(3)
        result_data = "Success via LocalStack"

        # 2. Update status to COMPLETED
        self.repository.update_status(job_id, JobStatus.COMPLETED, result_data)
        print(f"[Logic] Job {job_id} completed.")
