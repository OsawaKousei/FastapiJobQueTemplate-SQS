from typing import Optional, Protocol

from common.jobs.schemas import Job, JobStatus


class JobRepository(Protocol):
    def save(self, job: Job) -> Job: ...

    def get(self, job_id: str) -> Optional[Job]: ...

    def update_status(
        self, job_id: str, status: JobStatus, result: Optional[dict] = None
    ) -> None: ...
