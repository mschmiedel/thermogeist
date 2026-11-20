# SPDX-License-Identifier: MIT
"""Base entity for everything that belongs to a house device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import ThermogeistConfigEntry
from .const import DOMAIN, MANUFACTURER


class HouseEntity(Entity):
    """Entity attached to the house device (HAI-004, HAI-011)."""

    _attr_has_entity_name = True

    def __init__(self, entry: ThermogeistConfigEntry, key: str) -> None:
        self._entry = entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.runtime_data.house.name,
            manufacturer=MANUFACTURER,
            model="House",
        )
