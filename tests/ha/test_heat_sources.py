# SPDX-License-Identifier: MIT
"""Devices that heat the room (spec MDL-040, MDL-042 to MDL-044)."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, ROOM_SENSOR, setup_house
from .test_thermostats import FLOW_SENSOR, PLANNED, assign, z2m_device

PC = "sensor.gaming_pc_power"
HEAT = "sensor.living_room_heat_from_devices"


def report_pc(hass: HomeAssistant, watts: float) -> None:
    hass.states.async_set(PC, str(watts), {"device_class": "power", "unit_of_measurement": "W"})


async def test_room_dialog_asks_for_factors(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-008"""
    report_pc(hass, 300.0)
    entry = await setup_house(hass, HOUSE_WITH_LOAD)
    basics = {
        "name": "Living room",
        "temperature_entity": ROOM_SENSOR,
        "share_mode": "known",
        "design_indoor_temperature": 20.0,
        "heat_sources": [PC],
    }
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    assert result["last_step"] is False  # the factor step follows
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"known_share": 30.0}
    )
    assert result["step_id"] == "heat_source_factors"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {PC: 50.0})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["heat_sources"] == [{"entity": PC, "factor": 50.0}]
    assert float(hass.states.get(HEAT).state) == 150.0
    assert hass.states.get(HEAT).attributes["sources"] == {PC: 50.0}

    subentry_id = next(s for s in entry.subentries if entry.subentries[s].subentry_type == "room")
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "edit_room"}
    )
    marker = next(m for m in result["data_schema"].schema if str(m) == "heat_sources")
    assert marker.description == {"suggested_value": [PC]}


async def test_feed_forward_subtracts_device_heat(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-009"""
    report_pc(hass, 300.0)
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    room = {**LIVING_ROOM, "heat_sources": [{"entity": PC, "factor": 100.0}]}
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [room]
    )
    room_id = next(iter(entry.subentries))
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})
    await assign(hass, entry.entry_id, room_id, device_id, 1500.0)

    with_pc = hass.states.get(PLANNED).attributes
    assert with_pc["heat_from_devices_w"] == 300
    assert with_pc["demand_covered_by_devices_pct"] > 0

    report_pc(hass, 0.0)
    for _ in range(11):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    without_pc = hass.states.get(PLANNED).attributes
    assert without_pc["heat_from_devices_w"] == 0
    assert without_pc["feed_forward"] > with_pc["feed_forward"]


AC = "sensor.air_conditioner_power"
COP = "sensor.air_conditioner_cop_factor"


async def test_factor_entity_sets_heat_from_devices(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-012"""
    from custom_components.thermogeist.config_flow import factor_entity_key

    hass.states.async_set(AC, "500", {"device_class": "power", "unit_of_measurement": "W"})
    hass.states.async_set(COP, "420", {"unit_of_measurement": "%"})
    entry = await setup_house(hass, HOUSE_WITH_LOAD)
    basics = {
        "name": "Living room",
        "temperature_entity": ROOM_SENSOR,
        "share_mode": "known",
        "design_indoor_temperature": 20.0,
        "heat_sources": [AC],
    }
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"known_share": 30.0}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {AC: 400.0, factor_entity_key(AC): COP}
    )
    await hass.async_block_till_done()

    assert result["data"]["heat_sources"] == [{"entity": AC, "factor": 400.0, "factor_entity": COP}]
    assert float(hass.states.get(HEAT).state) == 2100.0
    assert hass.states.get(HEAT).attributes["sources"] == {AC: 420.0}
    assert hass.states.get(HEAT).attributes["factor_entities"] == {AC: COP}

    hass.states.async_set(COP, "unavailable")
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert float(hass.states.get(HEAT).state) == 2000.0
