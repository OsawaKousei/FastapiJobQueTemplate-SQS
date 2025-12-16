import uuid
from typing import Union

from common.jobs.queue import JobQueue
from common.jobs.repository import JobRepository
from common.jobs.schemas import Job, JobRequest, JobStatus
from common.shared.result import Failure, Success

Result = Union[Success[Job], Failure[Exception]]


class JobService:
    def __init__(self, repository: JobRepository, queue: JobQueue) -> None:
        self.repository = repository
        self.queue = queue

    def create_job(self, request: JobRequest) -> Result:
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            job_type=request.job_type,
            status=JobStatus.QUEUED,
            payload=request.payload,
        )

        try:
            self.repository.save(job)
            self.queue.send_message(job_id)
            return Success(job)
        except Exception as e:
            return Failure(e)

    def get_job(self, job_id: str) -> Union[Success[Job], Failure[str]]:
        job = self.repository.get(job_id)
        if job:
            return Success(job)
        return Failure("Job not found")
