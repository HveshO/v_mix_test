from fastapi import Depends, FastAPI, HTTPException, Path, Query
from sqlalchemy.orm import Session
import logging

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

logger = logging.getLogger(__name__)

app = FastAPI(title="Flaky Gate")


@app.post("/runs", response_model=CreateRunResponse)
def api_create_run(req: CreateRunRequest, db: Session = Depends(get_db)):
    try:
        run_id = services.create_run(db, branch=req.branch)
        return CreateRunResponse(runId=run_id)
    except Exception as e:
        logger.error("Error creating run: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/cases", response_model=CreateCaseResponse)
def api_create_case(req: CreateCaseRequest, db: Session = Depends(get_db)):
    try:
        case_id, external_id = services.create_case(
            db,
            external_id=req.externalId,
            name=req.name,
            owner=req.owner,
            is_quarantined=req.isQuarantined,
        )
        return CreateCaseResponse(id=case_id, externalId=external_id)
    except Exception as e:
        logger.error("Error creating case: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/runs/{run_id}/results", response_model=PostResultsResponse)
def api_post_results(
    run_id: int, items: list[PostResultItem], db: Session = Depends(get_db)
):
    run = services.get_run(db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_id not found in test_run")
    try:
        inserted = services.post_results(db, run_id=run_id, items=items)
        return PostResultsResponse(inserted=inserted)
    except Exception as e:
        logger.error("Error posting results for run %s: %s", run_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/runs/{run_id}/results/{result_id}", response_model=ResultResponse)
def api_get_result_by_id(
    run_id: int = Path(..., ge=0),
    result_id: int = Path(..., ge=0),
    db: Session = Depends(get_db),
):
    try:
        result = services.get_result_by_id(db, run_id=run_id, result_id=result_id)
        if not result:
            raise ValueError("Result not found in test_result")
        return ResultResponse(
            id=result.id,
            runId=result.run_id,
            externalId=result.external_id,
            status=result.status,
            durationMs=result.duration_ms,
            errorMessage=result.error_message,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Result not found")
    except Exception as e:
        logger.error(
            "Error getting result for run %s, index %s: %s", run_id, result_id, e
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/flaky", response_model=list[FlakyItem])
def api_get_flaky(
    window: int = Query(20, gt=0),
    minFailRate: float = Query(0.2, ge=0, le=1),
    owner: str | None = None,
    includeQuarantined: bool = False,
    limit: int = Query(50, gt=0, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    try:
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
    except Exception as e:
        logger.error("Error computing flaky stats: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
