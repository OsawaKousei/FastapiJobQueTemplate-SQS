from typing import Optional

from common.jobs.repository import JobRepository
from common.jobs.schemas import Job


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self._storage: dict[str, Job] = {}

    def save(self, job: Job) -> Job:
        self._storage[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._storage.get(job_id)

    def update_status(
        self, job_id: str, status: str, result: Optional[str] = None
    ) -> None:
        if job_id in self._storage:
            job = self._storage[job_id]
            # Create a new instance with updated fields (Job is likely a Pydantic model or dataclass)
            # Assuming Pydantic model based on usage
            updated_data = {"status": status}
            if result is not None:
                updated_data["result"] = result

            # Use model_copy for Pydantic v2 or copy for v1.
            # Since I don't know the exact Pydantic version, I'll assume standard Pydantic usage.
            # If it's a frozen dataclass or Pydantic model, we need to handle it correctly.
            # Let's check schemas.py content to be sure.

            # For now, I'll assume it's a Pydantic model and use model_copy(update=...) if v2 or copy(update=...) if v1.
            # Or just modify it if it's mutable.
            # Let's check schemas.py first.
            pass
