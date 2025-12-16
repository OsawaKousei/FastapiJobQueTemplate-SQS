from pydantic import BaseModel, ConfigDict

class JobAPayload(BaseModel):
    message: str
    
    model_config = ConfigDict(frozen=True)


class JobAResult(BaseModel):
    message: str
    status: str
    
    model_config = ConfigDict(frozen=True)
