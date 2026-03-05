from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import services
from app.schemas import (
    CreateRunRequest,
    CreateRunResponse,
    CreateCaseRequest,
    CreateCaseResponse,
    PostResultItem,
    PostResultsResponse,
    ResultResponse,
    FlakyItem,
)

app = FastAPI(title="Flaky Gate")


@app.post("/runs", response_model=CreateRunResponse)
def api_create_run(req: CreateRunRequest, db: Session = Depends(get_db)):
    run_id = services.create_run(db, branch=req.branch)
    return CreateRunResponse(runId=run_id)


@app.post("/cases", response_model=CreateCaseResponse)
def api_create_case(req: CreateCaseRequest, db: Session = Depends(get_db)):
    case_id, external_id = services.create_case(
        db,
        external_id=req.externalId,
        name=req.name,
        owner=req.owner,
        is_quarantined=req.isQuarantined,
    )
    return CreateCaseResponse(id=case_id, externalId=external_id)


@app.post("/runs/{run_id}/results", response_model=PostResultsResponse)
def api_post_results(run_id: int, items: list[PostResultItem], db: Session = Depends(get_db)):
    inserted = services.post_results(db, run_id=run_id, items=[i.model_dump() for i in items])
    return PostResultsResponse(inserted=inserted)


@app.get("/runs/{run_id}/results/{index}", response_model=ResultResponse)
def api_get_result_by_index(run_id: int, index: int, db: Session = Depends(get_db)):
    if index < 0:
        raise HTTPException(status_code=400, detail="index must be >= 0")

    r = services.get_result_by_index(db, run_id=run_id, index=index)
    return ResultResponse(
        id=r.id,
        runId=r.run_id,
        testExternalId=r.test_external_id,
        status=r.status,
        durationMs=r.duration_ms,
        errorMessage=r.error_message,
    )


@app.get("/flaky", response_model=list[FlakyItem])
def api_get_flaky(
    window: int = 20,
    minFailRate: float = 0.2,
    owner: str | None = None,
    includeQuarantined: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if limit <= 0 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be in (0..500]")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    if minFailRate < 0 or minFailRate > 1:
        raise HTTPException(status_code=400, detail="minFailRate must be in [0..1]")

    items = services.compute_flaky(
        db=db,
        window=window,
        min_fail_rate=minFailRate,
        owner=owner,
        include_quarantined=includeQuarantined,
        limit=limit,
        offset=offset,
    )
    return [FlakyItem(**i) for i in items]
