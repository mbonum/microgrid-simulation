"""Peer-to-peer energy matching and price discovery for the microgrid."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .actors import Actor


@dataclass
class Trade:
    seller_id: str
    buyer_id: str
    energy_kwh: float
    price_eur_kwh: float

    @property
    def value_eur(self) -> float:
        return self.energy_kwh * self.price_eur_kwh


@dataclass
class ExchangeResult:
    trades: List[Trade]
    unmet_demand_kwh: float   # demand that could not be matched locally
    excess_supply_kwh: float  # supply that could not be sold locally
    avg_price_eur_kwh: float  # volume-weighted average clearing price

    @property
    def total_volume_kwh(self) -> float:
        return sum(t.energy_kwh for t in self.trades)


def _midpoint_price(seller: Actor, buyer: Actor) -> float | None:
    """Return clearing price if seller/buyer prices overlap, else None."""
    if seller.max_sell_price_eur_kwh <= buyer.max_buy_price_eur_kwh:
        return (seller.max_sell_price_eur_kwh + buyer.max_buy_price_eur_kwh) / 2
    return None


def match_energy(actors: List[Actor], grid_fallback_price: float = 0.30) -> ExchangeResult:
    """
    Simple bilateral matching: sort sellers by ask price (ascending),
    buyers by bid price (descending), match greedily.
    Unmatched demand is served by the grid at grid_fallback_price.
    """
    sellers = [a for a in actors if a.net_kwh > 0]
    buyers  = [a for a in actors if a.net_kwh < 0]

    sellers.sort(key=lambda a: a.max_sell_price_eur_kwh)
    buyers.sort(key=lambda a: a.max_buy_price_eur_kwh, reverse=True)

    # mutable remaining supply/demand
    supply = {a.id: a.net_kwh for a in sellers}
    demand = {a.id: -a.net_kwh for a in buyers}

    trades: list[Trade] = []

    for seller in sellers:
        for buyer in buyers:
            if supply[seller.id] <= 0 or demand[buyer.id] <= 0:
                continue
            price = _midpoint_price(seller, buyer)
            if price is None:
                continue
            volume = min(supply[seller.id], demand[buyer.id])
            trade = Trade(seller.id, buyer.id, volume, price)
            trades.append(trade)
            supply[seller.id] -= volume
            demand[buyer.id]  -= volume

    # apply trades to actors
    actor_map = {a.id: a for a in actors}
    for t in trades:
        actor_map[t.seller_id].energy_sold_kwh += t.energy_kwh
        actor_map[t.seller_id].cost_eur        -= t.value_eur
        actor_map[t.buyer_id].energy_bought_kwh += t.energy_kwh
        actor_map[t.buyer_id].cost_eur          += t.value_eur

    # remaining demand → grid fallback
    unmet = sum(demand.values())
    for buyer in buyers:
        rem = demand[buyer.id]
        if rem > 0:
            actor_map[buyer.id].energy_bought_kwh += rem
            actor_map[buyer.id].cost_eur          += rem * grid_fallback_price

    excess = sum(supply.values())

    total_vol = sum(t.energy_kwh for t in trades)
    avg_price = (
        sum(t.energy_kwh * t.price_eur_kwh for t in trades) / total_vol
        if total_vol > 0 else 0.0
    )

    return ExchangeResult(trades, unmet, excess, avg_price)
