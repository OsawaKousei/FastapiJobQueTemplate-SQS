import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class GenerateSequenceRequest(BaseModel):
    length: int = Field(..., gt=0, description="Length of the sequence to generate")
    
    model_config = ConfigDict(frozen=True)

class SequenceResponse(BaseModel):
    task_id: str = Field(..., description="Unique ID for this task")
    job_id: str = Field(..., description="Associated background job ID")
    status: str = Field(..., description="Current status of the processing")
    squared_result: Optional[int] = Field(None, description="Result of the calculation")
    
    model_config = ConfigDict(frozen=True)
