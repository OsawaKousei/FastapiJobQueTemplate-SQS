import time
from typing import Any, Dict
from common.domain.job_a.job_schemas import JobAPayload

class JobAService:
    def process(self, payload: JobAPayload) -> Dict[str, Any]:
        time.sleep(1)
        return {"message": f"Processed Job A: {payload.message}", "status": "success"}
