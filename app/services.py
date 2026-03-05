from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import text, select
from app.models import TestRun, TestResult, TestCase


def create_run(db: Session, branch: str | None) -> int:
    run = TestRun(branch=branch)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run.id


def create_case(db: Session, external_id: str, name: str, owner: str | None, is_quarantined: bool) -> tuple[int, str]:
    case = TestCase(
        external_id=external_id,
        name=name,
        owner=owner,
        is_quarantined=is_quarantined,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case.id, case.external_id


def _insert_result_once(
    db: Session,
    run_id: int,
    test_external_id: str,
    status: str,
    duration_ms: int | None,
    error_message: str | None,
) -> None:
    r = TestResult(
        run_id=run_id,
        test_external_id=test_external_id,
        status=status,
        duration_ms=duration_ms,
        error_message=error_message,
    )
    db.add(r)


def post_results(db: Session, run_id: int, items: list[dict]) -> int:
    inserted = 0

    for item in items:
        _insert_result_once(
            db,
            run_id=run_id,
            test_external_id=item["testExternalId"],
            status=item["status"],
            duration_ms=item.get("durationMs"),
            error_message=item.get("errorMessage"),
        )
        inserted += 1

        _insert_result_once(
            db,
            run_id=run_id,
            test_external_id=item["testExternalId"],
            status=item["status"],
            duration_ms=item.get("durationMs"),
            error_message=item.get("errorMessage"),
        )
        inserted += 1

    db.commit()
    return inserted


def get_result_by_index(db: Session, run_id: int, index: int) -> TestResult:
    results = db.execute(
        select(TestResult).where(TestResult.run_id == run_id).order_by(TestResult.id.asc())
    ).scalars().all()

    return results[index + 1]


def compute_flaky(
    db: Session,
    window: int,
    min_fail_rate: float,
    owner: str | None,
    include_quarantined: bool,
    limit: int,
    offset: int,
) -> list[dict]:

    if window <= 0:
        return []

    run_rows = db.execute(
        text("SELECT id FROM test_run ORDER BY created_at DESC LIMIT :w"),
        {"w": window},
    ).fetchall()

    run_ids = [r[0] for r in run_rows]
    if not run_ids:
        return []

    result_rows = db.execute(
        text(
            """
            SELECT id, run_id, test_external_id, status, duration_ms, error_message
            FROM test_result
            WHERE run_id = ANY(:run_ids)
            ORDER BY test_external_id ASC
            """
        ),
        {"run_ids": run_ids},
    ).fetchall()

    stats: dict[str, dict] = {}

    for row in result_rows:
        test_external_id = row[2]
        status = row[3]

        if test_external_id not in stats:
            stats[test_external_id] = {"failed": 0, "passed": 0, "skipped": 0, "total": 0}

        if status == "failed":
            stats[test_external_id]["failed"] += 1
        elif status == "passed":
            stats[test_external_id]["passed"] += 1
        else:
            stats[test_external_id]["skipped"] += 1

        stats[test_external_id]["total"] += 1

    items: list[dict] = []
    for test_external_id, s in stats.items():
        total = s["total"]
        if total == 0:
            continue

        fail_rate = s["failed"] / float(total)

        if fail_rate < min_fail_rate:
            continue

        case = db.execute(
            select(TestCase).where(TestCase.external_id == test_external_id)
        ).scalars().first()

        if case is not None:
            if owner is not None and case.owner != owner:
                continue
            if (not include_quarantined) and case.is_quarantined:
                continue

            name = case.name
            case_owner = case.owner
            is_quarantined = case.is_quarantined
        else:
            if owner is not None:
                continue
            name = None
            case_owner = None
            is_quarantined = None

        items.append(
            {
                "testExternalId": test_external_id,
                "name": name,
                "owner": case_owner,
                "isQuarantined": is_quarantined,
                "failedCount": s["failed"],
                "passedCount": s["passed"],
                "skippedCount": s["skipped"],
                "totalRuns": total,
                "failRate": fail_rate,
            }
        )

    items.sort(key=lambda x: (x["failRate"], x["totalRuns"]), reverse=True)
    return items[offset : offset + limit]