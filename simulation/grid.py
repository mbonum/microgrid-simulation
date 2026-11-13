"""
SimPy-based microgrid simulation environment.
Runs through configurable timesteps, updates actor states, and calls
the exchange matching engine each step.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

import simpy

from .actors import Actor, ActorType, Battery
from .exchange import ExchangeResult, match_energy
from .metrics import (
    DailyMetrics,
    GridMetrics,
    compute_daily_metrics,
    compute_metrics,
)
from .profiles import commercial_load, residential_load, solar_profile


@dataclass
class SimConfig:
    n_prosumers: int = 5
    n_consumers: int = 5
    timestep_hours: float = 0.25        # 15-minute intervals
    duration_hours: float = 24.0
    grid_fallback_price: float = 0.30   # EUR/kWh
    seed: int = 42


@dataclass
class Snapshot:
    time_hours: float
    actor_states: list
    exchange: ExchangeResult
    metrics: GridMetrics


@dataclass
class SimState:
    config: SimConfig
    actors: list[Actor] = field(default_factory=list)
    snapshots: list[Snapshot] = field(default_factory=list)
    daily: DailyMetrics | None = None
    current_time: float = 0.0
    running: bool = False


def _make_actors(cfg: SimConfig, rng: random.Random) -> list[Actor]:
    actors = []
    for i in range(cfg.n_prosumers):
        bat = Battery(
            capacity_kwh=rng.uniform(5, 15),
            charge_kwh=rng.uniform(0, 5),
        )
        actors.append(Actor(
            id=f"prosumer-{i}",
            actor_type=ActorType.PROSUMER,
            battery=bat,
            max_sell_price_eur_kwh=rng.uniform(0.10, 0.18),
            max_buy_price_eur_kwh=rng.uniform(0.20, 0.28),
        ))
    for i in range(cfg.n_consumers):
        actors.append(Actor(
            id=f"consumer-{i}",
            actor_type=ActorType.CONSUMER,
            max_buy_price_eur_kwh=rng.uniform(0.22, 0.30),
            max_sell_price_eur_kwh=0.0,
        ))
    return actors


def run_simulation(
    cfg: SimConfig,
    on_step: Callable[[Snapshot], None] | None = None,
) -> SimState:
    """Run a full simulation synchronously; returns completed SimState."""
    rng = random.Random(cfg.seed)
    state = SimState(config=cfg, actors=_make_actors(cfg, rng))
    env = simpy.Environment()

    def _step(env: simpy.Environment) -> simpy.events.Process:
        while True:
            t = env.now * cfg.timestep_hours  # simulation time in hours
            state.current_time = t

            for actor in state.actors:
                actor.reset_timestep()
                noise = rng.gauss(1.0, 0.05)
                if actor.actor_type == ActorType.PROSUMER:
                    peak = rng.uniform(3, 8)
                    actor.production_kwh  = solar_profile(t, peak) * cfg.timestep_hours * noise
                    actor.consumption_kwh = residential_load(t) * cfg.timestep_hours * noise
                    # battery: charge surplus, discharge deficit
                    net = actor.net_kwh
                    if net > 0 and actor.battery:
                        stored = actor.battery.charge(net * 0.5)
                        actor.production_kwh -= stored
                    elif net < 0 and actor.battery:
                        delivered = actor.battery.discharge(-net * 0.5)
                        actor.production_kwh += delivered
                else:
                    actor.consumption_kwh = commercial_load(t) * cfg.timestep_hours * noise

            result = match_energy(state.actors, cfg.grid_fallback_price)
            metrics = compute_metrics(state.actors, result)

            snap = Snapshot(
                time_hours=t,
                actor_states=[
                    {
                        "id": a.id,
                        "type": a.actor_type,
                        "production_kwh": round(a.production_kwh, 4),
                        "consumption_kwh": round(a.consumption_kwh, 4),
                        "net_kwh": round(a.net_kwh, 4),
                        "soc": round(a.battery.soc, 3) if a.battery else None,
                        "cost_eur": round(a.cost_eur, 4),
                    }
                    for a in state.actors
                ],
                exchange=result,
                metrics=metrics,
            )
            state.snapshots.append(snap)
            if on_step:
                on_step(snap)

            yield env.timeout(1)

    env.process(_step(env))
    steps = int(cfg.duration_hours / cfg.timestep_hours)
    env.run(until=steps)
    state.daily = compute_daily_metrics(state.snapshots)
    state.running = False
    return state
