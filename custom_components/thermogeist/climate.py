# SPDX-License-Identifier: MIT
"""One climate entity per room: room temperature and setpoint (spec OVR-012).

In M2 the entity only holds the setpoint; nothing is written to thermostats yet.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .const import ROOM_SETPOINT_MAX_C, ROOM_SETPOINT_MIN_C, ROOM_SETPOINT_STEP_C
from .entity import RoomEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for room_id in entry.runtime_data.rooms:
        async_add_entities([RoomClimate(entry, room_id)], config_subentry_id=room_id)


class RoomClimate(RoomEntity, ClimateEntity):
    """The entity people and voice assistants use to set a room's temperature."""

    _attr_name = None
    _attr_hvac_mode = HVACMode.HEAT
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = ROOM_SETPOINT_MIN_C
    _attr_max_temp = ROOM_SETPOINT_MAX_C
    _attr_target_temperature_step = ROOM_SETPOINT_STEP_C

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "room")
        self._attr_hvac_modes = [HVACMode.HEAT]

    @property
    def current_temperature(self) -> float | None:
        return self.room_state.current_temperature_c

    @property
    def target_temperature(self) -> float:
        return self.room_state.user_setpoint_c

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.runtime.async_set_room_setpoint(self._room_id, float(temperature))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Only heating is supported; the house central mode switches rooms off."""
