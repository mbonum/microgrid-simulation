from simulation.grid import run_simulation, SimConfig


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
