"""KPI calculations for a single timestep exchange result."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .actors import Actor
from .exchange import ExchangeResult


@dataclass
class GridMetrics:
    self_sufficiency_ratio: float   # local demand met locally [0..1]
    self_consumption_ratio: float   # local supply consumed locally [0..1]
    total_cost_eur: float
    total_co2_saved_kg: float
    peer_traded_kwh: float


GRID_CO2_KG_PER_KWH = 0.233


def compute_metrics(actors: List[Actor], result: ExchangeResult) -> GridMetrics:
    total_demand = sum(a.consumption_kwh for a in actors)
    total_supply = sum(a.production_kwh  for a in actors)
    total_cost   = sum(a.cost_eur        for a in actors)

    peer_kwh  = result.total_volume_kwh
    unmet_kwh = result.unmet_demand_kwh

    self_suff = 1.0 - (unmet_kwh / total_demand) if total_demand > 0 else 1.0
    self_cons = peer_kwh / total_supply           if total_supply > 0 else 0.0
    co2_saved = peer_kwh * GRID_CO2_KG_PER_KWH

    return GridMetrics(
        self_sufficiency_ratio=round(max(0.0, min(1.0, self_suff)), 4),
        self_consumption_ratio=round(max(0.0, min(1.0, self_cons)), 4),
        total_cost_eur=round(total_cost, 4),
        total_co2_saved_kg=round(co2_saved, 4),
        peer_traded_kwh=round(peer_kwh, 4),
    )
