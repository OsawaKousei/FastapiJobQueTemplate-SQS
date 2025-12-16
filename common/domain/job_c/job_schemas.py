from typing import List
from pydantic import BaseModel, ConfigDict

class JobCPayload(BaseModel):
    tags: List[str]
    
    model_config = ConfigDict(frozen=True)
