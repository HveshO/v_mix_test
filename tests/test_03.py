from sqlalchemy import text
from app.db import engine


def test_03(client):
    run = client.post("/runs", json={"branch": "main"}).json()
    run_id = run["runId"]

    payload = [
        {"testExternalId": "t1", "status": "passed", "durationMs": 5},
        {"testExternalId": "t2", "status": "failed", "durationMs": 7},
        {"testExternalId": "t3", "status": "skipped", "durationMs": None},
    ]

    r = client.post(f"/runs/{run_id}/results", json=payload)
    assert r.status_code == 200

    with engine.connect() as c:
        cnt = c.execute(text("SELECT COUNT(*) FROM test_result WHERE run_id = :rid"), {"rid": run_id}).scalar_one()

    assert cnt == len(payload)