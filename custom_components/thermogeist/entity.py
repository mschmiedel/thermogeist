# SPDX-License-Identifier: MIT
"""Base entities for the house device and the room devices (spec HAI-004, HAI-005, HAI-011)."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from . import ThermogeistConfigEntry
from .const import DOMAIN, MANUFACTURER
from .core.actuator import Thermostat
from .house_config import room_area_id
from .runtime import HouseRuntime, RoomState, update_signal


class ThermogeistEntity(Entity):
    """Refreshes whenever the house runtime reports a change."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ThermogeistConfigEntry, key: str, unique_suffix: str) -> None:
        self._entry = entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{unique_suffix}_{key}"

    @property
    def runtime(self) -> HouseRuntime:
        return self._entry.runtime_data

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, update_signal(self._entry.entry_id), self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class HouseEntity(ThermogeistEntity):
    """Entity attached to the house device."""

    def __init__(self, entry: ThermogeistConfigEntry, key: str) -> None:
        super().__init__(entry, key, entry.entry_id)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.runtime_data.house.name,
            manufacturer=MANUFACTURER,
            model="Thermogeist House",
        )


class RoomEntity(ThermogeistEntity):
    """Entity attached to one room device, which hangs below the house device."""

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str, key: str) -> None:
        super().__init__(entry, key, room_id)
        self._room_id = room_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, room_id)},
            name=self.room_state.room.name,
            manufacturer=MANUFACTURER,
            model="Thermogeist Room",
            via_device_id=entry.runtime_data.house_device_id,
        )

    @property
    def room_state(self) -> RoomState:
        return self.runtime.rooms[self._room_id]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        area_id = room_area_id(self._entry, self._room_id)
        if area_id and self.device_entry and self.device_entry.area_id is None:
            area = ar.async_get(self.hass).async_get_area(area_id)
            if area is not None:
                dr.async_get(self.hass).async_update_device(self.device_entry.id, area_id=area_id)


class ThermostatEntity(RoomEntity):
    """Entity of one assigned thermostat, shown on the room device (HAI-006)."""

    def __init__(self, entry: ThermogeistConfigEntry, thermostat_id: str, key: str) -> None:
        thermostat = entry.runtime_data.thermostats[thermostat_id]
        super().__init__(entry, thermostat.room_id, key)
        self._thermostat_id = thermostat_id
        self._attr_unique_id = f"{thermostat_id}_{key}"
        self._attr_translation_placeholders = {"thermostat": thermostat.name}

    @property
    def thermostat(self) -> Thermostat:
        return self.runtime.thermostats[self._thermostat_id]
