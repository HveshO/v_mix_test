from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CreateRunRequest(BaseModel):
    branch: str | None = Field(None, max_length=128)


class CreateRunResponse(BaseModel):
    runId: int


class CreateCaseRequest(BaseModel):
    externalId: str = Field(..., max_length=512)
    name: str = Field(..., max_length=512)
    owner: str | None = Field(None, max_length=128)
    isQuarantined: bool = False


class CreateCaseResponse(BaseModel):
    id: int
    externalId: str


class StatusEnum(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PostResultItem(BaseModel):
    externalId: str = Field(..., max_length=512)
    status: StatusEnum
    durationMs: int | None = Field(None, ge=0)
    errorMessage: str | None = Field(None, max_length=4096)


class PostResultsResponse(BaseModel):
    inserted: int


class ResultResponse(BaseModel):
    id: int
    runId: int
    externalId: str
    status: str
    durationMs: int | None
    errorMessage: str | None


class FlakyItem(BaseModel):
    externalId: str
    name: str | None = None
    owner: str | None = None
    isQuarantined: bool | None = None
    failedCount: int
    passedCount: int
    skippedCount: int
    totalCount: int
    failRate: float
