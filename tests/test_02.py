def test_02(client):
    run = client.post("/runs", json={"branch": "main"}).json()
    run_id = run["runId"]

    client.post(
        f"/runs/{run_id}/results",
        json=[{"externalId": "t1", "status": "passed", "durationMs": 10}],
    )

    r = client.get(f"/runs/{run_id}/results/0")

    assert r.status_code == 200
