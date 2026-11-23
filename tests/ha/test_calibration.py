# SPDX-License-Identifier: MIT
"""Lost calibration in Home Assistant (spec DIA-024)."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.thermogeist.const import DOMAIN

from .test_thermostats import (
    assign,
    house_with_room,
    start_thermostat,
    suggested,
    thermostat_ids,
    z2m_device,
)

STEPS = "sensor.living_trv_closing_steps"
VALVE = "sensor.living_room_valve_position_living_trv"


async def test_lost_calibration_raises_an_issue(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CALIB-003"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(
        hass,
        "Living TRV",
        "SONOFF",
        "TRVZB",
        {
            "climate": ("climate", "heat"),
            "valve_opening_degree": ("number", "30", "%"),
            "valve_closing_degree": ("number", "70", "%"),
            "external_temperature_input": ("number", "20", "°C"),
            "closing_steps": ("sensor", "336"),
        },
    )
    hass.states.async_set("climate.living_trv_climate", "heat", {"hvac_action": "idle"})
    await assign(hass, entry.entry_id, room_id, device_id, 2000.0)
    tid = thermostat_ids(entry)[0]
    issue_id = f"thermostat_not_calibrated_{tid}"
    logbook = async_capture_events(hass, "logbook_entry")
    assert hass.states.get(VALVE).state == "30.0"

    hass.states.async_set(STEPS, "0")  # firmware update
    await hass.async_block_till_done()
    for _ in range(11):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None
    assert hass.states.get(VALVE).state == "unknown"
    assert any("Living TRV" in e.data["message"] for e in logbook)

    hass.states.async_set(STEPS, "337")  # button pressed, calibrated again
    await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
    assert hass.states.get(VALVE).state == "30.0"


async def test_values_can_be_set_for_a_device_without_profile(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CALIB-004"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(
        hass,
        "Old TRV",
        "Acme",
        "X1",
        {"climate": ("climate", "heat"), "calibration": ("sensor", "ok")},
    )
    status = "sensor.old_trv_calibration"
    form = await start_thermostat(hass, entry.entry_id, room_id, device_id)
    assert "uncalibrated_values" not in suggested(form)

    answers = {"climate": "climate.old_trv_climate", "more": {"uncalibrated_values": "Error"}}
    result = await hass.config_entries.subentries.async_configure(form["flow_id"], answers)
    assert result["errors"] == {"uncalibrated_values": "uncalibrated_needs_status"}

    answers["more"] = {"calibration_status": status, "uncalibrated_values": "error, lost"}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], answers)
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    tid = thermostat_ids(entry)[0]

    hass.states.async_set(status, "error")
    for _ in range(11):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"thermostat_not_calibrated_{tid}")
    assert issue is not None


async def test_profile_fills_in_the_values(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-CALIB-005"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(
        hass,
        "Living TRV",
        "SONOFF",
        "TRVZB",
        {
            "climate": ("climate", "heat"),
            "valve_opening_degree": ("number", "30", "%"),
            "valve_closing_degree": ("number", "70", "%"),
            "closing_steps": ("sensor", "336"),
        },
    )

    form = await start_thermostat(hass, entry.entry_id, room_id, device_id)

    assert suggested(form)["uncalibrated_values"] == "0"
    assert suggested(form)["calibration_status"] == STEPS
