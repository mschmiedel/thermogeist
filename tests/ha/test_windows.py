# SPDX-License-Identifier: MIT
"""Window delays per house and room, frost guard and the room window sensor (RUL-014, RUL-015)."""

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_capture_events

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, report_room_temperature, setup_house
from .test_control import REASON, WINDOW, tick

HOUSE_CLOSE = "number.home_window_close_after"
ROOM_CLOSE = "number.living_room_window_close_after"
ROOM_RESUME = "number.living_room_window_resume_heating_after"
RESET = "button.living_room_window_reset_times_to_house"
SENSOR = "binary_sensor.living_room_windows"


async def room_with_window(hass: HomeAssistant) -> None:
    hass.states.async_set(WINDOW, "off", {"device_class": "window"})
    await setup_house(hass, HOUSE_WITH_LOAD, [{**LIVING_ROOM, "window_sensors": [WINDOW]}])


async def set_number(hass: HomeAssistant, entity_id: str, value: float) -> None:
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": value}, blocking=True
    )


async def test_room_overrides_house_window_delay(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-010"""
    await room_with_window(hass)
    assert float(hass.states.get(HOUSE_CLOSE).state) == 30.0
    assert float(hass.states.get(ROOM_CLOSE).state) == 30.0
    assert hass.states.get(ROOM_CLOSE).attributes["source"] == "house"
    assert float(hass.states.get(ROOM_RESUME).state) == 10.0

    await set_number(hass, ROOM_CLOSE, 5.0)
    assert hass.states.get(ROOM_CLOSE).attributes["source"] == "room"
    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await tick(hass, freezer, 6)
    assert hass.states.get(REASON).state == "window_open"
    window = hass.states.get(SENSOR)
    assert window.state == "on"
    assert window.attributes["contacts"] == {WINDOW: "on"}
    assert window.attributes["heating_paused"] is True
    assert window.attributes["close_after_s"] == 5.0

    await hass.services.async_call("button", "press", {"entity_id": RESET}, blocking=True)
    assert float(hass.states.get(ROOM_CLOSE).state) == 30.0
    assert hass.states.get(ROOM_CLOSE).attributes["source"] == "house"


async def test_frost_guard_with_open_window(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-011"""
    await room_with_window(hass)
    logbook = async_capture_events(hass, "logbook_entry")
    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await tick(hass, freezer, 31)
    assert hass.states.get(SENSOR).attributes["frost_guard"] is False

    report_room_temperature(hass, 6.5)
    await tick(hass, freezer, 60)

    assert hass.states.get(REASON).state == "window_open"
    assert hass.states.get(REASON).attributes["frost_guard"] == "on"
    assert hass.states.get(SENSOR).attributes["frost_guard"] is True
    assert any("frost" in e.data["message"].lower() for e in logbook)
