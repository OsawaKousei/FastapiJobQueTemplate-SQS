from typing import List
from pydantic import BaseModel, ConfigDict

class JobCPayload(BaseModel):
    tags: List[str]
    
    model_config = ConfigDict(frozen=True)


class JobCResult(BaseModel):
    tag_count: int
    tags: List[str]
    status: str
    
    model_config = ConfigDict(frozen=True)
