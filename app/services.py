from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, text
from app.models import TestRun, TestResult, TestCase
from app.schemas import PostResultItem


def create_run(db: Session, branch: str | None) -> int:
    run = TestRun(branch=branch)
    db.add(run)
    db.flush()
    return run.id


def get_run(db: Session, run_id: int) -> TestRun | None:
    run = db.execute(select(TestRun).where(TestRun.id == run_id)).scalar_one_or_none()
    return run


def create_case(
    db: Session, external_id: str, name: str, owner: str | None, is_quarantined: bool
) -> tuple[int, str]:
    case = TestCase(
        external_id=external_id,
        name=name,
        owner=owner,
        is_quarantined=is_quarantined,
    )
    db.add(case)
    db.flush()
    return case.id, case.external_id


def post_results(db: Session, run_id: int, items: list[PostResultItem]) -> int:
    results = [
        TestResult(
            run_id=run_id,
            external_id=item.externalId,
            status=item.status,
            duration_ms=item.durationMs,
            error_message=item.errorMessage,
        )
        for item in items
    ]
    db.add_all(results)
    db.flush()
    return len(results)


def get_result_by_id(db: Session, run_id: int, result_id: int) -> TestResult:
    result = db.execute(
        select(TestResult).where(
            TestResult.run_id == run_id and TestResult.id == result_id
        )
    ).scalar_one_or_none()

    return result


def compute_flaky(
    db: Session,
    window: int,
    min_fail_rate: float,
    owner: str | None,
    include_quarantined: bool,
    limit: int,
    offset: int,
) -> list[dict]:

    sql = text(
        """
    WITH last_runs AS (
        SELECT id
        FROM test_run
        ORDER BY created_at DESC
        LIMIT :window
    ),
    stats AS (
        SELECT
            r.external_id,
            COUNT(*) FILTER (WHERE r.status = 'failed') AS failed_count,
            COUNT(*) FILTER (WHERE r.status = 'passed') AS passed_count,
            COUNT(*) FILTER (WHERE r.status = 'skipped') AS skipped_count,
            COUNT(*) AS total_count,
            COUNT(*) FILTER (WHERE r.status = 'failed')::float / NULLIF(COUNT(*), 0) AS fail_rate
        FROM test_result r
        WHERE r.run_id IN (SELECT id FROM last_runs)
        GROUP BY r.external_id
    )
    SELECT
        s.external_id as "externalId",
        tc.name,
        tc.owner,
        tc.is_quarantined as "isQuarantined",
        s.failed_count as "failedCount",
        s.passed_count as "passedCount",
        s.skipped_count as "skippedCount",
        s.total_count as "totalCount",
        s.fail_rate as "failRate"
    FROM stats s
    LEFT JOIN test_case tc
        ON tc.external_id = s.external_id
    WHERE s.fail_rate >= :min_fail_rate
    AND (:owner IS NULL OR tc.owner = :owner)
    AND (:include_quarantined OR tc.is_quarantined IS FALSE OR tc.is_quarantined IS NULL)
    ORDER BY s.fail_rate DESC, s.total_count DESC
    LIMIT :limit
    OFFSET :offset
    """
    )

    params = {
        "window": window,
        "min_fail_rate": min_fail_rate,
        "owner": owner,
        "include_quarantined": include_quarantined,
        "limit": limit,
        "offset": offset,
    }
    items = db.execute(sql, params).mappings().all()
    return items
