# SPDX-License-Identifier: MIT
"""Diagnostic sensors showing the house settings and profile defaults (spec HAI-004)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry, ThermogeistData
from .core.house import HeatingType
from .entity import HouseEntity

KELVIN_DIFFERENCE = "K"


@dataclass(frozen=True, kw_only=True)
class HouseSensorDescription(SensorEntityDescription):
    """Sensor description with a function that reads the value from the runtime data."""

    value: Callable[[ThermogeistData], str | float | None]


SENSORS: tuple[HouseSensorDescription, ...] = (
    HouseSensorDescription(
        key="heating_type",
        device_class=SensorDeviceClass.ENUM,
        options=[t.value for t in HeatingType],
        value=lambda d: d.house.heating_type.value,
    ),
    HouseSensorDescription(
        key="heat_load",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value=lambda d: d.house.heat_load_kw,
    ),
    HouseSensorDescription(
        key="design_outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda d: d.house.design_outdoor_temperature_c,
    ),
    HouseSensorDescription(
        key="share_outside",
        native_unit_of_measurement=PERCENTAGE,
        value=lambda d: d.house.share_outside_pct,
    ),
    HouseSensorDescription(
        key="min_valve_opening",
        native_unit_of_measurement=PERCENTAGE,
        value=lambda d: d.profile.min_valve_opening_pct,
    ),
    HouseSensorDescription(
        key="dead_band",
        native_unit_of_measurement=KELVIN_DIFFERENCE,
        value=lambda d: d.profile.dead_band_k,
    ),
    HouseSensorDescription(
        key="max_valve_change",
        native_unit_of_measurement=PERCENTAGE,
        value=lambda d: d.profile.max_valve_change_pct_per_30min,
    ),
    HouseSensorDescription(
        key="max_setback",
        native_unit_of_measurement=KELVIN_DIFFERENCE,
        value=lambda d: d.profile.max_setback_k,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(HouseSensor(entry, description) for description in SENSORS)


class HouseSensor(HouseEntity, SensorEntity):
    """Read-only view of one house setting."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    entity_description: HouseSensorDescription

    def __init__(self, entry: ThermogeistConfigEntry, description: HouseSensorDescription) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | float | None:
        return self.entity_description.value(self._entry.runtime_data)
