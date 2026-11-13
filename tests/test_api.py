from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_start_rejects_invalid_params():
    r = client.post("/simulation/start", json={"timestep_hours": 0})
    assert r.status_code == 422
    r = client.post("/simulation/start", json={"n_prosumers": -1})
    assert r.status_code == 422
    r = client.post("/simulation/start", json={"duration_hours": 100_000})
    assert r.status_code == 422


def test_start_and_daily_metrics_roundtrip():
    r = client.post(
        "/simulation/start",
        json={"n_prosumers": 2, "n_consumers": 2, "duration_hours": 1.0},
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    m = client.get(f"/simulation/{run_id}/metrics")
    assert m.status_code == 200
    fm = m.json()["final_metrics"]
    assert fm["peer_traded_kwh"] >= 0.0
    assert 0.0 <= fm["self_sufficiency_ratio"] <= 1.0
    assert 0.0 <= fm["self_consumption_ratio"] <= 1.0

    assert client.get("/simulation/nope/metrics").status_code == 404
