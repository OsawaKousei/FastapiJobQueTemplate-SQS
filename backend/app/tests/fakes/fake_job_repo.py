from typing import Optional

from common.jobs.repository import JobRepository
from common.jobs.schemas import Job, JobStatus


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
            update_data = {"status": JobStatus(status)}
            if result is not None:
                update_data["result"] = result

            self._storage[job_id] = job.model_copy(update=update_data)
