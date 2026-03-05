from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    branch: str | None = None


class CreateRunResponse(BaseModel):
    runId: int


class CreateCaseRequest(BaseModel):
    externalId: str
    name: str
    owner: str | None = None
    isQuarantined: bool = False


class CreateCaseResponse(BaseModel):
    id: int
    externalId: str


class PostResultItem(BaseModel):
    testExternalId: str
    status: str = Field(pattern="^(passed|failed|skipped)$")
    durationMs: int | None = None
    errorMessage: str | None = None


class PostResultsResponse(BaseModel):
    inserted: int


class ResultResponse(BaseModel):
    id: int
    runId: int
    testExternalId: str
    status: str
    durationMs: int | None
    errorMessage: str | None


class FlakyItem(BaseModel):
    testExternalId: str
    name: str | None = None
    owner: str | None = None
    isQuarantined: bool | None = None
    failedCount: int
    passedCount: int
    skippedCount: int
    totalRuns: int
    failRate: float