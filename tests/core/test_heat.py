# SPDX-License-Identifier: MIT
import pytest

from custom_components.thermogeist.core.heat import current_demand_w, room_heat_loss_w_per_k
from custom_components.thermogeist.core.house import HeatingType, House
from custom_components.thermogeist.core.room import Room

ROOM = Room(name="Room", temperature_entity="sensor.t")

HOUSE = House(
    name="Home",
    heating_type=HeatingType.HEAT_PUMP,
    outdoor_temperature_entity="sensor.outdoor",
    heat_load_kw=6.5,
    design_outdoor_temperature_c=-10.5,
)


def test_heat_loss_and_demand() -> None:
    """Scenario: SCN-HEAT-001"""
    heat_loss = room_heat_loss_w_per_k(HOUSE, ROOM, 12.5)
    assert heat_loss == pytest.approx(812.5 / 30.5)
    assert current_demand_w(heat_loss, 21.0, 5.0) == pytest.approx(812.5 / 30.5 * 16)
    assert current_demand_w(heat_loss, 21.0, 22.0) == 0.0


def test_no_heat_load_gives_no_watts() -> None:
    """Scenario: SCN-HEAT-002"""
    house = House(
        name="Home", heating_type=HeatingType.HEAT_PUMP, outdoor_temperature_entity="sensor.o"
    )
    heat_loss = room_heat_loss_w_per_k(house, ROOM, 12.5)
    assert heat_loss is None
    assert current_demand_w(heat_loss, 21.0, 5.0) is None


def test_design_indoor_temperature_changes_heat_loss_not_demand_target() -> None:
    """Scenario: SCN-HEAT-003"""
    bathroom = Room(name="Bath", temperature_entity="sensor.t", design_indoor_temperature_c=24.0)
    heat_loss = room_heat_loss_w_per_k(HOUSE, bathroom, 2.0)
    assert heat_loss == pytest.approx(130.0 / 34.5)
    assert current_demand_w(heat_loss, 21.0, 5.0) == pytest.approx(130.0 / 34.5 * 16)
