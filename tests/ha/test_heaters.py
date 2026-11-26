# SPDX-License-Identifier: MIT
"""Heaters with stages in Home Assistant (spec ACT-060 to ACT-069)."""

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.thermogeist.const import DOMAIN

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, report_room_temperature, setup_house

FLOW_SENSOR = "sensor.flow_temperature"
HEATER_SWITCH = "switch.plinth_fan"
STAGE_SENSOR = "sensor.plinth_stage"
PANEL_SWITCH = "input_boolean.infrared_panel"
CONTROL = "switch.living_room_control"


async def house(hass: HomeAssistant, rooms: list[dict[str, Any]] | None = None) -> MockConfigEntry:
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    return await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, rooms or [LIVING_ROOM]
    )


async def open_menu(hass: HomeAssistant, entry_id: str, room_id: str) -> dict[str, Any]:
    result = await hass.config_entries.subentries.async_init(
        (entry_id, "room"), context={"source": SOURCE_RECONFIGURE, "subentry_id": room_id}
    )
    assert result["type"] is FlowResultType.MENU
    return result


async def add_heater(
    hass: HomeAssistant, entry_id: str, room_id: str, answers: dict[str, Any]
) -> dict[str, Any]:
    """Room gear icon → Add heater → the heater form; returns the result after saving."""
    result = await open_menu(hass, entry_id, room_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "add_heater"}
    )
    assert result["step_id"] == "heater"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], answers)
    await hass.async_block_till_done()
    return result


def heater_id(entry: MockConfigEntry, room_id: str) -> str:
    return next(iter(entry.subentries[room_id].data["heaters"]))


def entity_for(hass: HomeAssistant, unique_id: str, domain: str = "sensor") -> str:
    entity_id = er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique_id)
    assert entity_id is not None, unique_id
    return entity_id


async def tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


CONVECTOR = {
    "name": "Plinth heater",
    "switch": HEATER_SWITCH,
    "energy_source": "heating_circuit",
    "stages": 2,
    "stage_outputs": "1300, 1700",
    "exponent": 1.0,
}


async def test_heater_is_added_and_mixing_is_rejected(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-HEATER-009"""
    kitchen = {
        **LIVING_ROOM,
        "name": "Kitchen",
        "thermostats": {"t1": {"name": "TRV", "roles": {"climate": "climate.kitchen_trv"}}},
    }
    entry = await house(hass, [LIVING_ROOM, kitchen])
    living_id, kitchen_id = list(entry.subentries)

    rejected = await add_heater(hass, entry.entry_id, living_id, CONVECTOR)
    assert rejected["errors"] == {"stage_sensor": "heater_needs_stage_entity"}
    saved = await hass.config_entries.subentries.async_configure(
        rejected["flow_id"], {**CONVECTOR, "stage_sensor": STAGE_SENSOR}
    )
    await hass.async_block_till_done()
    assert saved["reason"] == "reconfigure_successful"

    hid = heater_id(entry, living_id)
    stored = entry.subentries[living_id].data["heaters"][hid]
    assert stored["stage_outputs"] == [1300.0, 1700.0]
    assert stored["stage_sensor"] == STAGE_SENSOR
    assert hass.states.get(entity_for(hass, f"{hid}_heater_stage")) is not None
    assert hass.states.get(entity_for(hass, f"{living_id}_planned_heat_share")) is not None

    menu = await open_menu(hass, entry.entry_id, kitchen_id)
    assert "add_heater" not in menu["menu_options"]
    living_menu = await open_menu(hass, entry.entry_id, living_id)
    assert "add_thermostat" not in living_menu["menu_options"]
    result = await hass.config_entries.subentries.async_configure(
        living_menu["flow_id"], {"next_step_id": "edit_heater"}
    )
    assert result["step_id"] == "edit_heater"


async def test_control_switches_heater_and_restores_it(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-HEATER-010"""
    report_room_temperature(hass, 15.0)
    hass.states.async_set(PANEL_SWITCH, "off")
    entry = await house(hass)
    room_id = next(iter(entry.subentries))
    panel = {
        "name": "Panel",
        "switch": PANEL_SWITCH,
        "energy_source": "direct",
        "stages": 1,
        "stage_outputs": "1000",
    }
    assert (await add_heater(hass, entry.entry_id, room_id, panel))["reason"] == (
        "reconfigure_successful"
    )
    # An input_boolean as switch: the mocks must not catch Thermogeist's own control switch.
    on = async_mock_service(hass, "input_boolean", "turn_on")
    off = async_mock_service(hass, "input_boolean", "turn_off")
    hid = heater_id(entry, room_id)
    stage = entity_for(hass, f"{hid}_heater_stage")

    await tick(hass, freezer, 180)
    assert on == off == []
    assert hass.states.get(stage).attributes["planned_stage"] == 1
    assert hass.states.get(stage).attributes["mode"] == "observe"

    await hass.services.async_call("switch", "turn_on", {"entity_id": CONTROL}, blocking=True)
    await tick(hass, freezer, 91)
    # The mocked service does not change the state, so it may be sent again each apply.
    assert {c.data["entity_id"] for c in on} == {PANEL_SWITCH}

    await hass.services.async_call("switch", "turn_off", {"entity_id": CONTROL}, blocking=True)
    await hass.async_block_till_done()
    assert {c.data["entity_id"] for c in off} == {PANEL_SWITCH}


async def test_heater_sensor_output_and_fault(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-HEATER-011"""
    hass.states.async_set(HEATER_SWITCH, "on")
    hass.states.async_set(STAGE_SENSOR, "2")
    entry = await house(hass)
    room_id = next(iter(entry.subentries))
    await add_heater(hass, entry.entry_id, room_id, {**CONVECTOR, "stage_sensor": STAGE_SENSOR})
    hid = heater_id(entry, room_id)
    stage = entity_for(hass, f"{hid}_heater_stage")
    estimated = entity_for(hass, f"{room_id}_estimated_output")
    problem = entity_for(hass, f"{hid}_heater_not_running", "binary_sensor")
    await tick(hass, freezer, 60)

    expected = 1700 * (40.0 - 2.5 - 19.5) / 49.8
    assert hass.states.get(stage).state == "2"
    assert hass.states.get(stage).attributes["heat_output_w"] == round(expected)
    assert float(hass.states.get(estimated).state) == pytest.approx(round(expected))

    hass.states.async_set(STAGE_SENSOR, "0")
    await tick(hass, freezer, 60)
    assert hass.states.get(problem).state == "off"
    await tick(hass, freezer, 180)
    assert hass.states.get(problem).state == "on"
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"heater_not_running_{hid}") is not None
    assert float(hass.states.get(estimated).state) == 0

    hass.states.async_set(STAGE_SENSOR, "1")
    await hass.async_block_till_done()
    assert hass.states.get(problem).state == "off"
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"heater_not_running_{hid}") is None
