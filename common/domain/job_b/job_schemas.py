from pydantic import BaseModel, ConfigDict


class JobBPayload(BaseModel):
    count: int

    model_config = ConfigDict(frozen=True)


class JobBResult(BaseModel):
    count_squared: int
    status: str

    model_config = ConfigDict(frozen=True)
