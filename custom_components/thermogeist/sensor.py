# SPDX-License-Identifier: MIT
"""Sensors of the house and of each room (spec HAI-004, MDL-010, MDL-011, MDL-035, RSN-002)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ThermogeistConfigEntry
from .const import DOCS_URL
from .core.decisions import ReasonCode
from .core.house import HeatingType
from .core.room import ShareMode
from .entity import HouseEntity, RoomEntity
from .runtime import HouseRuntime, RoomState

WATT_PER_KELVIN = "W/K"


@dataclass(frozen=True, kw_only=True)
class HouseSensorDescription(SensorEntityDescription):
    value: Callable[[HouseRuntime], str | float | None]


@dataclass(frozen=True, kw_only=True)
class RoomSensorDescription(SensorEntityDescription):
    value: Callable[[RoomState], str | float | None]
    attributes: Callable[[RoomState, HouseRuntime], dict[str, Any]] | None = None


HOUSE_SENSORS: tuple[HouseSensorDescription, ...] = (
    HouseSensorDescription(
        key="heating_type",
        device_class=SensorDeviceClass.ENUM,
        options=[t.value for t in HeatingType],
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda r: r.house.heating_type.value,
    ),
    HouseSensorDescription(
        key="heat_load",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda r: r.house.heat_load_kw,
    ),
    HouseSensorDescription(
        key="design_outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda r: r.house.design_outdoor_temperature_c,
    ),
    HouseSensorDescription(
        key="share_outside",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda r: r.house.share_outside_pct,
    ),
    HouseSensorDescription(
        key="unassigned_share",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda r: r.shares.unassigned_pct,
    ),
)


def _share_attributes(state: RoomState, runtime: HouseRuntime) -> dict[str, Any]:
    return {
        "source": state.room.share_mode.value,
        "scaled_down": state.room.share_mode is ShareMode.ESTIMATED and runtime.shares.scaled_down,
    }


def _reason_attributes(state: RoomState, runtime: HouseRuntime) -> dict[str, Any]:
    decision = state.decision
    if decision is None:
        return {}
    return {
        "severity": decision.severity.value,
        "since": decision.timestamp.isoformat(),
        "faq": f"{DOCS_URL}/en/faq/{decision.code.value}.md",
        **decision.params,
    }


ROOM_SENSORS: tuple[RoomSensorDescription, ...] = (
    RoomSensorDescription(
        key="active_reason",
        device_class=SensorDeviceClass.ENUM,
        options=[code.value for code in ReasonCode],
        value=lambda s: s.decision.code.value if s.decision else None,
        attributes=_reason_attributes,
    ),
    RoomSensorDescription(
        key="target_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda s: s.decision.target_setpoint_c if s.decision else None,
    ),
    RoomSensorDescription(
        key="heat_demand",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda s: s.demand_w,
    ),
    RoomSensorDescription(
        key="room_share",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda s: s.share_pct,
        attributes=_share_attributes,
    ),
    RoomSensorDescription(
        key="heat_loss_coefficient",
        native_unit_of_measurement=WATT_PER_KELVIN,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda s: s.heat_loss_w_per_k,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(HouseSensor(entry, description) for description in HOUSE_SENSORS)
    for room_id in entry.runtime_data.rooms:
        async_add_entities(
            (RoomSensor(entry, room_id, description) for description in ROOM_SENSORS),
            config_subentry_id=room_id,
        )


class HouseSensor(HouseEntity, SensorEntity):
    entity_description: HouseSensorDescription

    def __init__(self, entry: ThermogeistConfigEntry, description: HouseSensorDescription) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | float | None:
        return self.entity_description.value(self.runtime)


class RoomSensor(RoomEntity, SensorEntity):
    entity_description: RoomSensorDescription

    def __init__(
        self, entry: ThermogeistConfigEntry, room_id: str, description: RoomSensorDescription
    ) -> None:
        super().__init__(entry, room_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | float | None:
        return self.entity_description.value(self.room_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes is None:
            return None
        return self.entity_description.attributes(self.room_state, self.runtime)
