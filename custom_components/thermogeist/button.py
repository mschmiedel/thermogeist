# SPDX-License-Identifier: MIT
"""Reset the control settings to the profile of the heating type (spec CTL-014)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .entity import HouseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ResetControlSettingsButton(entry)])


class ResetControlSettingsButton(HouseEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ThermogeistConfigEntry) -> None:
        super().__init__(entry, "reset_control_settings")

    async def async_press(self) -> None:
        await self.runtime.async_reset_overrides()
