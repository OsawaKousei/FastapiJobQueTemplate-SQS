import time
from typing import Any, Dict
from common.domain.job_b.job_schemas import JobBPayload

class JobBService:
    def process(self, payload: JobBPayload) -> Dict[str, Any]:
        time.sleep(2)
        return {"count_squared": payload.count * payload.count, "status": "success"}
