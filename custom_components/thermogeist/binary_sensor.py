# SPDX-License-Identifier: MIT
"""Windows and doors of a room at a glance (spec RUL-010, RUL-014, RUL-015)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .core.decisions import ReasonCode
from .core.profiles import ControlSetting
from .entity import HeaterEntity, RoomEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for room_id, state in entry.runtime_data.rooms.items():
        if state.room.window_entities:
            async_add_entities([RoomWindowSensor(entry, room_id)], config_subentry_id=room_id)
    for heater_id, heater in entry.runtime_data.heaters.items():
        if heater.stage_sensor:
            async_add_entities(
                [HeaterProblemSensor(entry, heater_id)], config_subentry_id=heater.room_id
            )


class HeaterProblemSensor(HeaterEntity, BinarySensorEntity):
    """ACT-064: on while the heater is switched on but its stage sensor says nothing runs."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry: ThermogeistConfigEntry, heater_id: str) -> None:
        super().__init__(entry, heater_id, "heater_not_running")

    @property
    def is_on(self) -> bool:
        return self.runtime.heater_live[self._heater_id].fault


class RoomWindowSensor(RoomEntity, BinarySensorEntity):
    """On while any contact of the room is open; attributes say what Thermogeist does."""

    _attr_device_class = BinarySensorDeviceClass.WINDOW

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "windows")

    @property
    def is_on(self) -> bool:
        return any(
            (s := self.hass.states.get(entity)) is not None and s.state == STATE_ON
            for entity in self.room_state.room.window_entities
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        decision = self.room_state.decision
        heating_paused = decision is not None and decision.code is ReasonCode.WINDOW_OPEN
        return {
            "contacts": {
                entity: (s.state if (s := self.hass.states.get(entity)) else None)
                for entity in self.room_state.room.window_entities
            },
            "heating_paused": heating_paused,
            "frost_guard": heating_paused and "frost_guard" in decision.params,
            "close_after_s": self.runtime.window_setting(
                self._room_id, ControlSetting.WINDOW_CLOSE_AFTER
            )[0],
            "resume_after_s": self.runtime.window_setting(
                self._room_id, ControlSetting.WINDOW_RESUME_AFTER
            )[0],
        }
