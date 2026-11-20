# SPDX-License-Identifier: MIT
import pytest

from custom_components.thermogeist.core.heat import current_demand_w, room_heat_loss_w_per_k
from custom_components.thermogeist.core.house import HeatingType, House

HOUSE = House(
    name="Home",
    heating_type=HeatingType.HEAT_PUMP,
    outdoor_temperature_entity="sensor.outdoor",
    heat_load_kw=6.5,
    design_outdoor_temperature_c=-10.5,
)


def test_heat_loss_and_demand() -> None:
    """Scenario: SCN-HEAT-001"""
    heat_loss = room_heat_loss_w_per_k(HOUSE, 12.5)
    assert heat_loss == pytest.approx(812.5 / 30.5)
    assert current_demand_w(heat_loss, 21.0, 5.0) == pytest.approx(812.5 / 30.5 * 16)
    assert current_demand_w(heat_loss, 21.0, 22.0) == 0.0


def test_no_heat_load_gives_no_watts() -> None:
    """Scenario: SCN-HEAT-002"""
    house = House(
        name="Home", heating_type=HeatingType.HEAT_PUMP, outdoor_temperature_entity="sensor.o"
    )
    heat_loss = room_heat_loss_w_per_k(house, 12.5)
    assert heat_loss is None
    assert current_demand_w(heat_loss, 21.0, 5.0) is None
