# SPDX-License-Identifier: MIT
"""Per room: observe or control, and the child lock (spec ACT-040, ACT-044, OVR-022)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .entity import RoomEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for room_id in entry.runtime_data.rooms:
        async_add_entities([ControlSwitch(entry, room_id)], config_subentry_id=room_id)
        if room_id in entry.runtime_data.child_lock.rooms:
            async_add_entities([ChildLockSwitch(entry, room_id)], config_subentry_id=room_id)


class ControlSwitch(RoomEntity, SwitchEntity):
    """Off: Thermogeist only observes. On: it writes to the room's valve-based thermostats."""

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "control")

    @property
    def is_on(self) -> bool:
        return self.runtime.control.is_enabled(self._room_id)

    @property
    def available(self) -> bool:
        return bool(self.room_state.thermostat_ids)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"can_control": self.runtime.control.can_control(self._room_id)}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.runtime.control.async_set_enabled(self._room_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.runtime.control.async_set_enabled(self._room_id, False)


class ChildLockSwitch(RoomEntity, SwitchEntity):
    """OVR-022: the child lock of all thermostats of the room, kept on by Thermogeist.

    Off while unlocked for 30 minutes (OVR-023): it shows what applies right now.
    """

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "child_lock")

    @property
    def is_on(self) -> bool:
        lock = self.runtime.child_lock
        return lock.is_on(self._room_id) and lock.unlocked_until(self._room_id) is None

    @property
    def available(self) -> bool:
        return self.runtime.child_lock.available(self._room_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.runtime.child_lock.async_set(self._room_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.runtime.child_lock.async_set(self._room_id, False)
