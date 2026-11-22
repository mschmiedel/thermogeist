# SPDX-License-Identifier: MIT
"""Heating water and room coverage on the house device (spec DIA-042, MDL-046)."""

from homeassistant.core import HomeAssistant

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, setup_house
from .test_thermostats import FLOW_SENSOR, RETURN_SENSOR


async def test_heating_water_and_coverage(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-HOUSE-007"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    hass.states.async_set(RETURN_SENSOR, "34.0", {"device_class": "temperature"})
    house = {
        **HOUSE_WITH_LOAD,
        "flow_temperature_entity": FLOW_SENSOR,
        "return_temperature_entity": RETURN_SENSOR,
    }
    await setup_house(hass, house, [LIVING_ROOM])

    assert float(hass.states.get("sensor.home_flow_temperature").state) == 40.0
    assert float(hass.states.get("sensor.home_return_temperature").state) == 34.0
    spread = hass.states.get("sensor.home_spread")
    assert float(spread.state) == 6.0
    assert spread.attributes["flow"] == FLOW_SENSOR

    coverage = hass.states.get("sensor.home_room_coverage")
    unassigned = float(hass.states.get("sensor.home_heat_load_not_assigned_to_a_room").state)
    assert float(coverage.state) == 100.0 - unassigned
    assert coverage.attributes["rooms"] == 1
    assert coverage.attributes["floor_area_not_in_rooms_m2"] == 160.0 - 20.0


async def test_no_water_sensors_without_sources(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-HOUSE-008"""
    await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])

    assert hass.states.get("sensor.home_flow_temperature") is None
    assert hass.states.get("sensor.home_spread") is None
    assert hass.states.get("sensor.home_room_coverage") is not None


async def test_flow_from_the_heating_curve(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-HOUSE-013"""
    house = {
        **HOUSE_WITH_LOAD,
        "curve_cold_outdoor": -10.0,
        "curve_cold_flow": 45.0,
        "curve_warm_outdoor": 15.0,
        "curve_warm_flow": 30.0,
    }
    await setup_house(hass, house, [LIVING_ROOM])

    # 5 °C outside lies 15 K above the cold point: 45 - 15/25 x 15 = 36 °C.
    flow = hass.states.get("sensor.home_flow_temperature")
    assert float(flow.state) == 36.0
    assert flow.attributes["source"] == "heating_curve"
    # The design day (-10.5 °C) is colder than the cold point: the curve stays at 45 °C.
    design = hass.states.get("sensor.home_flow_on_the_design_day")
    assert float(design.state) == 45.0
    assert design.attributes["source"] == "heating_curve"
    assert hass.states.get("sensor.home_spread") is None
