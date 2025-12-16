# ruff: noqa: N815
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SQSRecord(BaseModel):
    messageId: str
    receiptHandle: str
    body: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    messageAttributes: Dict[str, Any] = Field(default_factory=dict)
    eventSource: str
    awsRegion: str


class SQSEvent(BaseModel):
    Records: List[SQSRecord] = Field(default_factory=list)
