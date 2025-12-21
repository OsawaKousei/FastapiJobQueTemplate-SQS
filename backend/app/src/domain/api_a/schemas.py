from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Message content to process")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1-5)")

    model_config = ConfigDict(frozen=True)


class MessageResponse(BaseModel):
    request_id: str = Field(..., description="Unique ID for this request")
    job_id: str = Field(..., description="Associated background job ID")
    status: str = Field(..., description="Current status of the processing")
    text: str = Field(..., description="Original text")
    processed_message: Optional[str] = Field(
        None, description="Result message from worker"
    )

    model_config = ConfigDict(frozen=True)
