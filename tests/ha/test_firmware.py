# SPDX-License-Identifier: MIT
"""Minimum firmware in Home Assistant (spec ACT-017, ACT-105)."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir

from custom_components.thermogeist.const import DOMAIN

from .test_thermostats import assign, house_with_room, sonoff, thermostat_ids


async def test_old_firmware_raises_a_warning_until_updated(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-FW-002"""
    entry, room_id = await house_with_room(hass)
    device_id = sonoff(hass)
    devices = dr.async_get(hass)
    devices.async_update_device(device_id, sw_version="1.1.4")

    await assign(hass, entry.entry_id, room_id, device_id, 2000.0)
    await hass.async_block_till_done()
    tid = thermostat_ids(entry)[0]
    issue_id = f"thermostat_firmware_old_{entry.entry_id}_{tid}"
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.severity is ir.IssueSeverity.WARNING
    assert issue.translation_placeholders["installed"] == "1.1.4"
    assert issue.translation_placeholders["required"] == "1.3.0"

    devices.async_update_device(device_id, sw_version="1.3.0")
    await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None
