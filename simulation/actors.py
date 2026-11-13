"""Prosumer, Consumer, and Battery models for the microgrid simulation."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActorType(str, Enum):
    PROSUMER = "prosumer"   # produces + consumes (e.g. solar panel owner)
    CONSUMER = "consumer"   # consumes only


@dataclass
class Battery:
    """Simple battery storage model."""
    capacity_kwh: float           # max storable energy
    charge_kwh: float = 0.0       # current charge
    charge_rate_kw: float = 5.0   # max charge/discharge power per timestep
    efficiency: float = 0.95      # round-trip efficiency

    @property
    def soc(self) -> float:
        """State of charge [0..1]."""
        return self.charge_kwh / self.capacity_kwh if self.capacity_kwh > 0 else 0.0

    def charge(self, energy_kwh: float) -> float:
        """Charge battery; returns actual energy stored."""
        available = min(energy_kwh * self.efficiency, self.capacity_kwh - self.charge_kwh)
        stored = min(available, self.charge_rate_kw)
        self.charge_kwh += stored
        return stored / self.efficiency  # energy drawn from source

    def discharge(self, energy_kwh: float) -> float:
        """Discharge battery; returns actual energy delivered."""
        available = min(self.charge_kwh * self.efficiency, energy_kwh)
        delivered = min(available, self.charge_rate_kw)
        self.charge_kwh -= delivered / self.efficiency
        return delivered


@dataclass
class Actor:
    """A participant in the microgrid."""
    id: str
    actor_type: ActorType
    # Energy state for current timestep (kWh)
    production_kwh: float = 0.0
    consumption_kwh: float = 0.0
    battery: Optional[Battery] = None
    # Accounting
    energy_bought_kwh: float = 0.0
    energy_sold_kwh: float = 0.0
    cost_eur: float = 0.0         # negative = earned
    # Preferences
    max_sell_price_eur_kwh: float = 0.15
    max_buy_price_eur_kwh: float = 0.25

    @property
    def net_kwh(self) -> float:
        """Positive = surplus (can sell), negative = deficit (needs to buy)."""
        return self.production_kwh - self.consumption_kwh

    def reset_timestep(self) -> None:
        self.production_kwh = 0.0
        self.consumption_kwh = 0.0
