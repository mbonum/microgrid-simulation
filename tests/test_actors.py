from simulation.actors import Actor, ActorType, Battery


def test_battery_charge_discharge():
    bat = Battery(capacity_kwh=10.0, charge_kwh=0.0)
    drawn = bat.charge(5.0)
    assert drawn > 0
    assert 0 < bat.charge_kwh <= 5.0

    delivered = bat.discharge(3.0)
    assert delivered > 0
    assert bat.charge_kwh < 5.0


def test_actor_net_kwh():
    a = Actor(id="p0", actor_type=ActorType.PROSUMER,
              production_kwh=3.0, consumption_kwh=1.5)
    assert a.net_kwh == 1.5


def test_battery_soc_bounds():
    bat = Battery(capacity_kwh=10.0, charge_kwh=5.0)
    assert 0 <= bat.soc <= 1
    bat.charge(100)  # overcharge attempt
    assert bat.charge_kwh <= bat.capacity_kwh
