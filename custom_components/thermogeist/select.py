# SPDX-License-Identifier: MIT
"""Central mode of the house (spec RUL-003)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ThermogeistConfigEntry
from .core.house import CentralMode
from .entity import HouseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([CentralModeSelect(entry)])


class CentralModeSelect(HouseEntity, SelectEntity, RestoreEntity):
    """Auto / stop / frost protection for the whole house. Survives restarts."""

    def __init__(self, entry: ThermogeistConfigEntry) -> None:
        super().__init__(entry, "central_mode")
        self._attr_options = [mode.value for mode in CentralMode]

    @property
    def current_option(self) -> str:
        return self.runtime.central_mode.value

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in self._attr_options:
            self.runtime.set_central_mode(CentralMode(last.state))

    async def async_select_option(self, option: str) -> None:
        self.runtime.set_central_mode(CentralMode(option))
