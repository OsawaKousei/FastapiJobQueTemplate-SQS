from pydantic import BaseModel, ConfigDict

class JobAPayload(BaseModel):
    message: str
    
    model_config = ConfigDict(frozen=True)
