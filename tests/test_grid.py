import pytest

from simulation.grid import SimConfig, run_simulation


def test_simulation_runs():
    cfg = SimConfig(n_prosumers=2, n_consumers=2, duration_hours=2.0, seed=1)
    state = run_simulation(cfg)
    expected_steps = int(cfg.duration_hours / cfg.timestep_hours)
    assert len(state.snapshots) == expected_steps


def test_metrics_range():
    cfg = SimConfig(n_prosumers=3, n_consumers=3, duration_hours=1.0, seed=7)
    state = run_simulation(cfg)
    for snap in state.snapshots:
        m = snap.metrics
        assert 0.0 <= m.self_sufficiency_ratio <= 1.0
        assert 0.0 <= m.self_consumption_ratio <= 1.0
        assert m.total_co2_saved_kg >= 0.0


def test_daily_metrics_aggregate_full_day():
    cfg = SimConfig(n_prosumers=3, n_consumers=3, duration_hours=24.0, seed=42)
    state = run_simulation(cfg)
    assert state.daily is not None
    peer = sum(s.exchange.total_volume_kwh for s in state.snapshots)
    assert state.daily.peer_traded_kwh == pytest.approx(peer, abs=1e-3)
    assert state.daily.total_co2_saved_kg == pytest.approx(
        state.daily.peer_traded_kwh * 0.233, abs=1e-3
    )
    assert 0.0 <= state.daily.self_sufficiency_ratio <= 1.0
    assert 0.0 <= state.daily.self_consumption_ratio <= 1.0
    # the last snapshot is a night step with no solar; the day total must exceed it
    assert state.daily.peer_traded_kwh > state.snapshots[-1].metrics.peer_traded_kwh
