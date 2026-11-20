# SPDX-License-Identifier: MIT
"""Sensors of the house, each room and each thermostat (spec HAI-004 to HAI-006, ACT-014,
ACT-015, MDL-010, MDL-011, MDL-035, RSN-002, CTL-035)."""

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
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import ThermogeistConfigEntry
from .const import DOCS_URL
from .core.actuator import Kind, Role
from .core.decisions import ReasonCode
from .core.house import HeatingType
from .core.room import ShareMode
from .entity import HouseEntity, RoomEntity, ThermostatEntity
from .runtime import HouseRuntime, RoomState, numeric_state

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
    for room_id, state in entry.runtime_data.rooms.items():
        sensors: list[SensorEntity] = [
            RoomSensor(entry, room_id, description) for description in ROOM_SENSORS
        ]
        if state.thermostat_ids:
            sensors.append(PlannedValveSensor(entry, room_id))
        async_add_entities(sensors, config_subentry_id=room_id)
    for thermostat_id, thermostat in entry.runtime_data.thermostats.items():
        thermostat_sensors: list[SensorEntity] = [ThermostatKindSensor(entry, thermostat_id)]
        if Role.VALVE_READ in thermostat.roles:
            thermostat_sensors.append(ThermostatValveSensor(entry, thermostat_id))
        # A device belongs to one sub-entry: thermostat sensors live on the room device, so they
        # are registered under the room's sub-entry. Removed thermostats are cleaned up on setup.
        async_add_entities(thermostat_sensors, config_subentry_id=thermostat.room_id)


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


class PlannedValveSensor(RoomEntity, SensorEntity):
    """Observe mode: the valve position Thermogeist would set, with its parts (CTL-035)."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "planned_valve_position")

    @property
    def native_value(self) -> float | None:
        plan = self.room_state.plan
        return plan.output_pct if plan else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        plan = self.room_state.plan
        thermostats = [self.runtime.thermostats[t] for t in self.room_state.thermostat_ids]
        attributes: dict[str, Any] = {
            "mode": "observe",
            "strategies": sorted({t.kind.value for t in thermostats}),
            "radiator_output_w": self.room_state.rated_output_w,
        }
        if plan is not None:
            attributes |= {
                "feed_forward": round(plan.feed_forward_pct, 1),
                "proportional": round(plan.proportional_pct, 1),
                "integral": round(plan.integral_pct, 1),
                "limits": [limit.value for limit in plan.limits],
            }
        return attributes


class ThermostatKindSensor(ThermostatEntity, SensorEntity):
    """Which kind, profile and roles a thermostat has (ACT-033)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: ThermogeistConfigEntry, thermostat_id: str) -> None:
        super().__init__(entry, thermostat_id, "thermostat_kind")
        self._attr_options = [kind.value for kind in Kind]

    @property
    def native_value(self) -> str:
        return self.thermostat.kind.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "profile": self.thermostat.profile_id,
            "radiator_output_w": self.thermostat.rated_output_w,
            "roles": {role.value: entity for role, entity in self.thermostat.roles.items()},
        }


class ThermostatValveSensor(ThermostatEntity, SensorEntity):
    """The thermostat's actual valve position, next to the planned one (ACT-015)."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: ThermogeistConfigEntry, thermostat_id: str) -> None:
        super().__init__(entry, thermostat_id, "thermostat_valve_position")

    @property
    def _source(self) -> str:
        return self.thermostat.roles[Role.VALVE_READ]

    @property
    def native_value(self) -> float | None:
        return numeric_state(self.hass, self._source)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source], self._source_changed)
        )

    @callback
    def _source_changed(self, _event: Event[EventStateChangedData]) -> None:
        self.async_write_ha_state()
