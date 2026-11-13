import pytest

from simulation.actors import Actor, ActorType
from simulation.exchange import match_energy


def _make(id_, prod, cons, sell_price=0.15, buy_price=0.25):
    return Actor(
        id=id_, actor_type=ActorType.PROSUMER if prod > 0 else ActorType.CONSUMER,
        production_kwh=prod, consumption_kwh=cons,
        max_sell_price_eur_kwh=sell_price,
        max_buy_price_eur_kwh=buy_price,
    )


def test_basic_trade():
    seller = _make("s0", prod=5.0, cons=1.0)   # net +4
    buyer  = _make("b0", prod=0.0, cons=3.0)   # net -3
    result = match_energy([seller, buyer])
    assert len(result.trades) == 1
    assert result.trades[0].energy_kwh == pytest.approx(3.0, abs=1e-6)


def test_no_trade_price_mismatch():
    seller = _make("s0", prod=5.0, cons=1.0, sell_price=0.28)
    buyer  = _make("b0", prod=0.0, cons=3.0, buy_price=0.20)
    result = match_energy([seller, buyer])
    assert len(result.trades) == 0
    assert result.unmet_demand_kwh > 0


def test_unmet_demand_goes_to_grid():
    buyer = _make("b0", prod=0.0, cons=5.0)
    result = match_energy([buyer], grid_fallback_price=0.30)
    assert result.unmet_demand_kwh == pytest.approx(5.0, abs=1e-6)
    assert buyer.cost_eur == pytest.approx(5.0 * 0.30, abs=1e-4)
