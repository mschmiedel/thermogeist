# SPDX-License-Identifier: MIT
"""Thermogeist: Home Assistant integration.

This module is the thin HA layer. All domain logic lives in ``core`` and must not import
anything from ``homeassistant`` (spec ARC-001).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, MANUFACTURER, SUBENTRY_ROOM, SUBENTRY_THERMOSTAT
from .device_profiles import async_get_profiles
from .house_config import (
    house_from_entry,
    migrate_thermostat_subentries,
    rooms_from_entry,
    thermostats_from_entry,
)
from .runtime import HouseRuntime
from .z2m import async_track_devices

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type ThermogeistConfigEntry = ConfigEntry[HouseRuntime]


async def async_migrate_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """1.1 → 1.2: thermostats move from their own sub-entries into their room (HAI-007)."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        rooms = {
            sid: s.data for sid, s in entry.subentries.items() if s.subentry_type == SUBENTRY_ROOM
        }
        thermostats = {
            sid: (s.title, s.data)
            for sid, s in entry.subentries.items()
            if s.subentry_type == SUBENTRY_THERMOSTAT
        }
        for room_id, data in migrate_thermostat_subentries(rooms, thermostats).items():
            hass.config_entries.async_update_subentry(entry, entry.subentries[room_id], data=data)
        for thermostat_id in thermostats:
            hass.config_entries.async_remove_subentry(entry, thermostat_id)
        hass.config_entries.async_update_entry(entry, minor_version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """Set up one house with its rooms."""
    runtime = HouseRuntime(
        hass,
        entry.entry_id,
        house_from_entry(entry),
        rooms_from_entry(entry),
        thermostats_from_entry(entry),
        profiles=await async_get_profiles(hass),
    )
    await async_track_devices(hass)
    await runtime.async_load()
    runtime.house_device_id = _house_device(hass, entry).id
    entry.runtime_data = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _remove_stale_entities(hass, entry)
    runtime.async_start()
    entry.async_on_unload(runtime.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_change))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> bool:
    """Unload one house; its state is written at once (CTL-040), not after the save delay."""
    await entry.runtime_data.async_flush()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> None:
    """Delete stored settings when the house is removed."""
    await HouseRuntime(hass, entry.entry_id, house_from_entry(entry), {}).async_remove()


def _house_device(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> dr.DeviceEntry:
    """Create the house device up front so rooms can link to it by id."""
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=house_from_entry(entry).name,
        manufacturer=MANUFACTURER,
        model="Thermogeist House",
    )


def _remove_stale_entities(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> None:
    """HAI-017: drop entities this setup did not create.

    That covers removed rooms and thermostats as well as entities a thermostat no longer has
    after editing (e.g. its valve position once no position can be read).
    """
    created = entry.runtime_data.created_unique_ids
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id not in created:
            registry.async_remove(entity.entity_id)


async def _async_reload_on_change(hass: HomeAssistant, entry: ThermogeistConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
