# SPDX-License-Identifier: MIT
"""Control mode against a simulated Bosch BTH-RA (spec ACT-040 to ACT-045, OVR-001, RUL-010)."""

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, setup_house
from .test_thermostats import FLOW_SENSOR, assign, z2m_device

SWITCH = "switch.living_room_control"
REASON = "sensor.living_room_active_reason"
VALVE = "number.bath_trv_pi_heating_demand"
REMOTE = "number.bath_trv_remote_temperature"
MODE = "select.bath_trv_operating_mode"
DEVICE_CLIMATE = "climate.bath_trv_climate"
WINDOW = "binary_sensor.living_room_window"


class Calls:
    def __init__(self, hass: HomeAssistant) -> None:
        self.number = async_mock_service(hass, "number", "set_value")
        self.select = async_mock_service(hass, "select", "select_option")
        self.climate = async_mock_service(hass, "climate", "set_temperature")

    @staticmethod
    def values(calls: list[ServiceCall], entity_id: str, key: str) -> list[Any]:
        return [c.data[key] for c in calls if c.data["entity_id"] == entity_id]


async def controlled_bosch(hass: HomeAssistant, windows: bool = False) -> tuple[Any, Calls]:
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    room = {**LIVING_ROOM, "window_sensors": [WINDOW]} if windows else LIVING_ROOM
    if windows:
        hass.states.async_set(WINDOW, "off", {"device_class": "window"})
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [room]
    )
    room_id = next(iter(entry.subentries))
    device_id = z2m_device(
        hass,
        "Bath TRV",
        "Bosch",
        "BTH-RA",
        {
            "climate": ("climate", "heat"),
            "pi_heating_demand": ("number", "39", "%"),
            "remote_temperature": ("number", "20", "°C"),
            "operating_mode": ("select", "schedule"),
        },
    )
    hass.states.async_set(DEVICE_CLIMATE, "heat", {"temperature": 20.0})
    await assign(hass, entry.entry_id, room_id, device_id, 700.0)
    calls = Calls(hass)
    return entry, calls


async def tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def switch(hass: HomeAssistant, on: bool) -> None:
    await hass.services.async_call(
        "switch", "turn_on" if on else "turn_off", {"entity_id": SWITCH}, blocking=True
    )


async def test_observe_mode_writes_nothing(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CONTROL-001"""
    _, calls = await controlled_bosch(hass)

    await tick(hass, freezer, 180)

    assert hass.states.get(SWITCH).state == "off"
    assert calls.number == calls.select == calls.climate == []


async def test_control_writes_after_startup_hold(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CONTROL-002"""
    _, calls = await controlled_bosch(hass)

    await switch(hass, True)
    assert hass.states.get(REASON).state == "startup_hold"
    assert calls.number == []

    await tick(hass, freezer, 91)

    assert hass.states.get(REASON).state == "setpoint"
    assert Calls.values(calls.select, MODE, "option") == ["manual"]
    planned = float(hass.states.get("sensor.living_room_planned_valve_position").state)
    assert Calls.values(calls.number, VALVE, "value") == [planned]
    assert Calls.values(calls.number, REMOTE, "value") == [19.5]
    assert calls.climate == []  # device already shows 20 °C


async def test_switching_off_restores_the_device(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CONTROL-003"""
    _, calls = await controlled_bosch(hass)
    await switch(hass, True)
    await tick(hass, freezer, 91)

    await switch(hass, False)

    assert Calls.values(calls.select, MODE, "option") == ["manual", "schedule"]
    assert Calls.values(calls.number, VALVE, "value")[-1] == 39.0


async def test_gives_up_when_device_keeps_regulating(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CONTROL-004"""
    entry, calls = await controlled_bosch(hass)
    await switch(hass, True)
    await tick(hass, freezer, 91)
    hass.states.async_set(VALVE, "14", {"unit_of_measurement": "%"})
    logbook = async_capture_events(hass, "logbook_entry")

    for _ in range(40):
        await tick(hass, freezer, 60)

    written = Calls.values(calls.number, VALVE, "value")
    assert len(written) >= 4
    assert written[:4] == [written[0]] * 4  # first write + three rewrites of the same value
    assert hass.states.get(SWITCH).state == "off"
    thermostat_id = next(s for s, e in entry.subentries.items() if e.subentry_type == "thermostat")
    issue = ir.async_get(hass).async_get_issue(
        "thermogeist", f"device_overrides_valve_{thermostat_id}"
    )
    assert issue is not None
    assert any("Bath TRV" in e.data["message"] for e in logbook)


async def test_setpoint_on_device_becomes_room_setpoint(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CONTROL-005"""
    await controlled_bosch(hass)
    await switch(hass, True)
    await tick(hass, freezer, 91)
    logbook = async_capture_events(hass, "logbook_entry")

    hass.states.async_set(DEVICE_CLIMATE, "heat", {"temperature": 22.0})
    await tick(hass, freezer, 10)
    assert hass.states.get("climate.living_room").attributes["temperature"] == 20.0
    await tick(hass, freezer, 11)

    assert hass.states.get("climate.living_room").attributes["temperature"] == 22.0
    assert any("22.0" in e.data["message"] for e in logbook)


async def test_window_closes_valve_and_reopens(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CONTROL-006"""
    _, calls = await controlled_bosch(hass, windows=True)
    await switch(hass, True)
    await tick(hass, freezer, 91)
    before = Calls.values(calls.number, VALVE, "value")[-1]

    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await tick(hass, freezer, 31)
    assert hass.states.get(REASON).state == "window_open"
    assert Calls.values(calls.number, VALVE, "value")[-1] == 0.0

    hass.states.async_set(WINDOW, "off", {"device_class": "window"})
    await hass.async_block_till_done()
    assert hass.states.get(REASON).state == "setpoint"
    assert Calls.values(calls.number, VALVE, "value")[-1] == pytest.approx(before, abs=1)


async def test_setpoint_only_room_cannot_be_controlled(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-CONTROL-007"""
    entry = await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])
    room_id = next(iter(entry.subentries))
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})
    await assign(hass, entry.entry_id, room_id, device_id, None)

    with pytest.raises(HomeAssistantError):
        await switch(hass, True)
    assert hass.states.get(SWITCH).state == "off"
