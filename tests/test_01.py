def test_01(client):
    run = client.post("/runs", json={"branch": "main"}).json()
    run_id = run["runId"]

    client.post(
        "/cases",
        json={"externalId": "t1", "name": "test_one", "owner": "qa", "isQuarantined": False},
    )

    client.post(
        f"/runs/{run_id}/results",
        json=[{"testExternalId": "t1", "status": "failed", "durationMs": 10}],
    )

    r = client.get("/flaky?window=0&minFailRate=0.1")
    assert r.status_code == 200

    data = r.json()

    assert len(data) == 1