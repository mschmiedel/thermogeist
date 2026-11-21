# SPDX-License-Identifier: MIT
"""Estimated radiator output per room (spec MDL-013)."""

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant

from .test_control import VALVE, controlled_bosch, tick

OUTPUT = "sensor.living_room_estimated_radiator_output"


async def test_estimated_output_from_reported_valve(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-013"""
    await controlled_bosch(hass)
    hass.states.async_set(VALVE, "39", {"unit_of_measurement": "%"})
    await tick(hass, freezer, 61)

    state = hass.states.get(OUTPUT)
    assert float(state.state) == pytest.approx(106, abs=1)
    assert state.attributes["max_output_w"] == pytest.approx(186, abs=1)
    assert state.attributes["radiators"]["Bath TRV"]["valve_pct"] == 39
    assert state.attributes["radiators"]["Bath TRV"]["valve_source"] == "reported"
    assert "missing" not in state.attributes

    hass.states.async_set(VALVE, "unavailable")
    await tick(hass, freezer, 61)
    state = hass.states.get(OUTPUT)
    assert state.state == "unknown"
    assert state.attributes["missing"] == ["valve_position"]


async def test_house_shows_demand_and_supply_of_rooms(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-HOUSE-009"""
    await controlled_bosch(hass)
    hass.states.async_set(VALVE, "39", {"unit_of_measurement": "%"})
    await tick(hass, freezer, 61)

    demand = hass.states.get("sensor.home_heat_demand_of_rooms")
    radiators = hass.states.get("sensor.home_estimated_radiator_output_of_rooms")
    devices = hass.states.get("sensor.home_heat_from_devices_of_rooms")
    assert float(demand.state) == pytest.approx(
        float(hass.states.get("sensor.living_room_heat_demand").state), abs=1
    )
    assert float(radiators.state) == pytest.approx(float(hass.states.get(OUTPUT).state), abs=1)
    assert float(devices.state) == 0
    assert radiators.attributes["rooms"] == 1
    assert radiators.attributes["rooms_without_estimate"] == []
