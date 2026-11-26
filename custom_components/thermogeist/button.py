# SPDX-License-Identifier: MIT
"""Reset buttons (CTL-014, RUL-014, LRN-036) and the short child lock unlock (OVR-023)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .entity import HouseEntity, RoomEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ResetControlSettingsButton(entry)])
    for room_id, state in entry.runtime_data.rooms.items():
        if state.room.window_entities:
            async_add_entities([ResetRoomWindowButton(entry, room_id)], config_subentry_id=room_id)
        if state.has_actuators:
            async_add_entities([ResetLearningButton(entry, room_id)], config_subentry_id=room_id)
        if room_id in entry.runtime_data.child_lock.rooms:
            async_add_entities([UnlockChildLockButton(entry, room_id)], config_subentry_id=room_id)


class ResetControlSettingsButton(HouseEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ThermogeistConfigEntry) -> None:
        super().__init__(entry, "reset_control_settings")

    async def async_press(self) -> None:
        await self.runtime.async_reset_overrides()


class ResetRoomWindowButton(RoomEntity, ButtonEntity):
    """RUL-014: the room's window delays follow the house again."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "reset_window_delays")

    async def async_press(self) -> None:
        await self.runtime.async_reset_room_overrides(self._room_id)


class ResetLearningButton(RoomEntity, ButtonEntity):
    """LRN-036: the room starts learning what it really needs again."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "reset_learning")

    async def async_press(self) -> None:
        await self.runtime.async_reset_learning(self._room_id)


class UnlockChildLockButton(RoomEntity, ButtonEntity):
    """OVR-023: child lock off for 30 minutes, e.g. for a battery change."""

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "unlock_child_lock")

    @property
    def available(self) -> bool:
        lock = self.runtime.child_lock
        return lock.available(self._room_id) and lock.is_on(self._room_id)

    async def async_press(self) -> None:
        await self.runtime.child_lock.async_unlock_for_a_while(self._room_id)
