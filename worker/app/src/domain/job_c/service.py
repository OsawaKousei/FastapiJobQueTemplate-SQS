import time
from typing import Any, Dict
from common.domain.job_c.job_schemas import JobCPayload

class JobCService:
    def process(self, payload: JobCPayload) -> Dict[str, Any]:
        time.sleep(3)
        return {"tag_count": len(payload.tags), "tags": payload.tags, "status": "success"}
