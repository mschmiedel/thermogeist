# SPDX-License-Identifier: MIT
"""Thermogeist: Home Assistant integration.

This module is the thin HA layer. All domain logic lives in ``core`` and must not import
anything from ``homeassistant`` (spec ARC-001).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .house_config import house_from_entry, rooms_from_entry
from .runtime import HouseRuntime

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

type ThermogeistConfigEntry = ConfigEntry[HouseRuntime]


async def async_setup_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """Set up one house with its rooms."""
    runtime = HouseRuntime(hass, entry.entry_id, house_from_entry(entry), rooms_from_entry(entry))
    await runtime.async_load()
    entry.runtime_data = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    runtime.async_start()
    entry.async_on_unload(runtime.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_change))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """Unload one house."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> None:
    """Delete stored settings when the house is removed."""
    await HouseRuntime(hass, entry.entry_id, house_from_entry(entry), {}).async_remove()


async def _async_reload_on_change(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
