import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class TaggingRequest(BaseModel):
    raw_tags: str = Field(..., description="Comma separated tags")
    
    model_config = ConfigDict(frozen=True)

class TaggingResponse(BaseModel):
    request_id: str = Field(..., description="Unique ID for this request")
    job_id: str = Field(..., description="Associated background job ID")
    status: str = Field(..., description="Current status of the processing")
    tag_count: Optional[int] = Field(None, description="Number of tags processed")
    tags: Optional[List[str]] = Field(None, description="List of processed tags")
    
    model_config = ConfigDict(frozen=True)
