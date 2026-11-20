# SPDX-License-Identifier: MIT
"""Thermogeist: Home Assistant integration.

This module is the thin HA layer. All domain logic lives in ``core`` and must not import
anything from ``homeassistant`` (spec ARC-001).
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .core.house import House
from .core.profiles import Profile, profile_for
from .house_config import house_from_entry

PLATFORMS: list[Platform] = [Platform.SELECT, Platform.SENSOR]


@dataclass(slots=True)
class ThermogeistData:
    """Runtime data of one house."""

    house: House
    profile: Profile


type ThermogeistConfigEntry = ConfigEntry[ThermogeistData]


async def async_setup_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """Set up one house."""
    house = house_from_entry(entry)
    entry.runtime_data = ThermogeistData(house=house, profile=profile_for(house.heating_type))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_change))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """Unload one house."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_on_change(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
