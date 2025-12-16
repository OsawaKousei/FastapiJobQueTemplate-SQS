from typing import Optional, Protocol

from common.jobs.schemas import Job


class JobRepository(Protocol):
    def save(self, job: Job) -> Job: ...

    def get(self, job_id: str) -> Optional[Job]: ...

    def update_status(
        self, job_id: str, status: str, result: Optional[dict] = None
    ) -> None: ...
