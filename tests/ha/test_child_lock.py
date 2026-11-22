# SPDX-License-Identifier: MIT
"""Smart child lock in Home Assistant, in observe mode (spec OVR-022 to OVR-024)."""

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Event, HomeAssistant, callback
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from .test_thermostats import assign, house_with_room, sonoff

DEVICE_LOCK = "switch.living_trv_child_lock"
ROOM_LOCK = "switch.living_room_child_lock"
UNLOCK = "button.living_room_child_lock_off_for_30_min"
BACK_ON = "sensor.living_room_child_lock_back_on"


class Device:
    """The thermostat's child lock switch: records writes and reports the new state."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.writes: list[str] = []
        hass.bus.async_listen(EVENT_CALL_SERVICE, self._on_call)

    @callback
    def _on_call(self, event: Event) -> None:
        data = event.data
        entity_ids = data["service_data"].get("entity_id")
        if data["domain"] != "switch" or entity_ids != DEVICE_LOCK:
            return
        state = "on" if data["service"] == "turn_on" else "off"
        self.writes.append(state)
        self.hass.states.async_set(DEVICE_LOCK, state)


async def room_with_sonoff(
    hass: HomeAssistant, lock: str = "off"
) -> tuple[MockConfigEntry, Device]:
    entry, room_id = await house_with_room(hass)
    device_id = sonoff(hass)
    hass.states.async_set(DEVICE_LOCK, lock)
    await assign(hass, entry.entry_id, room_id, device_id, 2000.0)
    return entry, Device(hass)


async def switch_room(hass: HomeAssistant, on: bool) -> None:
    await hass.services.async_call(
        "switch", "turn_on" if on else "turn_off", {"entity_id": ROOM_LOCK}, blocking=True
    )
    await hass.async_block_till_done()


async def device_reports(hass: HomeAssistant, state: str) -> None:
    hass.states.async_set(DEVICE_LOCK, state)
    await hass.async_block_till_done()


async def tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory, minutes: float) -> None:
    freezer.tick(timedelta(minutes=minutes))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


def messages(events: list[Any]) -> list[str]:
    return [e.data["message"] for e in events]


async def test_room_switch_keeps_the_lock_on(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-LOCK-007"""
    _, device = await room_with_sonoff(hass)
    logbook = async_capture_events(hass, "logbook_entry")
    assert hass.states.get(ROOM_LOCK).state == "off"
    assert hass.states.get(UNLOCK).state == "unavailable"

    await switch_room(hass, True)
    assert device.writes == ["on"]

    await device_reports(hass, "off")  # firmware update
    assert device.writes == ["on", "on"]
    assert any("Living TRV" in m for m in messages(logbook))

    await switch_room(hass, False)
    assert device.writes == ["on", "on", "off"]
    assert hass.states.get(ROOM_LOCK).state == "off"


async def test_lock_at_the_device_switches_the_room_on(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-LOCK-008"""
    _, device = await room_with_sonoff(hass)
    logbook = async_capture_events(hass, "logbook_entry")

    await device_reports(hass, "on")

    assert hass.states.get(ROOM_LOCK).state == "on"
    assert device.writes == []
    assert any("Living TRV" in m for m in messages(logbook))


async def test_existing_lock_is_taken_over(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-LOCK-009"""
    _, device = await room_with_sonoff(hass, lock="on")

    assert hass.states.get(ROOM_LOCK).state == "on"
    assert device.writes == []


async def test_unlock_for_30_minutes_survives_a_restart(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-LOCK-010"""
    entry, device = await room_with_sonoff(hass, lock="on")
    logbook = async_capture_events(hass, "logbook_entry")

    await hass.services.async_call("button", "press", {"entity_id": UNLOCK}, blocking=True)
    await hass.async_block_till_done()
    assert device.writes == ["off"]
    assert hass.states.get(ROOM_LOCK).state == "off"
    assert hass.states.get(BACK_ON).state not in ("unknown", "unavailable")

    await tick(hass, freezer, 10)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await tick(hass, freezer, 10)
    assert device.writes == ["off"]

    await tick(hass, freezer, 11)
    assert device.writes == ["off", "on"]
    assert hass.states.get(ROOM_LOCK).state == "on"
    assert hass.states.get(BACK_ON).state == "unknown"
    assert len(messages(logbook)) == 2


async def test_switching_on_ends_the_30_minutes(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-LOCK-011"""
    _, device = await room_with_sonoff(hass, lock="on")
    await hass.services.async_call("button", "press", {"entity_id": UNLOCK}, blocking=True)
    await hass.async_block_till_done()

    await switch_room(hass, True)

    assert device.writes == ["off", "on"]
    assert hass.states.get(ROOM_LOCK).state == "on"
    assert hass.states.get(BACK_ON).state == "unknown"
