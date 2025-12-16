from typing import List

from common.domain.job_a.job_schemas import JobAPayload, JobAResult
from common.domain.job_b.job_schemas import JobBPayload, JobBResult
from common.domain.job_c.job_schemas import JobCPayload, JobCResult
from src.domain.job_a.service import JobAService
from src.domain.job_b.service import JobBService
from src.domain.job_c.service import JobCService


class FakeJobAService(JobAService):
    def __init__(self):
        self.processed_payloads: List[JobAPayload] = []

    def process(self, payload: JobAPayload) -> JobAResult:
        self.processed_payloads.append(payload)
        return JobAResult(
            message=f"Fake processed: {payload.message}", status="success"
        )


class FakeJobBService(JobBService):
    def __init__(self):
        self.processed_payloads: List[JobBPayload] = []

    def process(self, payload: JobBPayload) -> JobBResult:
        self.processed_payloads.append(payload)
        return JobBResult(
            count_squared=payload.count * 2, status="success"
        )  # Fake logic


class FakeJobCService(JobCService):
    def __init__(self):
        self.processed_payloads: List[JobCPayload] = []

    def process(self, payload: JobCPayload) -> JobCResult:
        self.processed_payloads.append(payload)
        return JobCResult(
            tag_count=999, tags=payload.tags, status="success"
        )  # Fake logic
