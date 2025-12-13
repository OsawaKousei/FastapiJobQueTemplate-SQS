from typing import Protocol, Optional
from app.src.domain.jobs.schemas import Job

class JobRepository(Protocol):
    def save(self, job: Job) -> Job:
        ...

    def get(self, job_id: str) -> Optional[Job]:
        ...

    def update_status(self, job_id: str, status: str, result: Optional[str] = None) -> None:
        ...
