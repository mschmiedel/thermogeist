# SPDX-License-Identifier: MIT
"""Editable control settings of the house (spec CTL-014, RUL-002)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .core.profiles import LIMITS, ControlSetting
from .entity import HouseEntity

KELVIN_DIFFERENCE = "K"

UNITS: dict[ControlSetting, str] = {
    ControlSetting.MIN_VALVE_OPENING: PERCENTAGE,
    ControlSetting.DEAD_BAND: KELVIN_DIFFERENCE,
    ControlSetting.MAX_VALVE_CHANGE: PERCENTAGE,
    ControlSetting.MAX_SETBACK: KELVIN_DIFFERENCE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(ControlSettingNumber(entry, setting) for setting in ControlSetting)


class ControlSettingNumber(HouseEntity, NumberEntity):
    """Starts at the profile default; a value set here overrides it until reset."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ThermogeistConfigEntry, setting: ControlSetting) -> None:
        super().__init__(entry, setting.value)
        self._setting = setting
        limits = LIMITS[setting]
        self._attr_native_min_value = limits.minimum
        self._attr_native_max_value = limits.maximum
        self._attr_native_step = limits.step
        self._attr_native_unit_of_measurement = UNITS[setting]

    @property
    def native_value(self) -> float:
        return self.runtime.settings()[self._setting].value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"source": self.runtime.settings()[self._setting].source.value}

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.async_set_override(self._setting, value)
