from pydantic import BaseModel, ConfigDict

class JobBPayload(BaseModel):
    count: int
    
    model_config = ConfigDict(frozen=True)
