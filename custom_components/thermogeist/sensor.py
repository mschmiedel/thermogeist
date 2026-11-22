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
from .core.actuator import Kind, Role, derives_valve
from .core.decisions import ReasonCode
from .core.house import HeatingType
from .core.room import ShareMode
from .core.sizing import Sizing, SizingResult
from .entity import HouseEntity, RoomEntity, ThermostatEntity
from .runtime import HouseRuntime, RoomState

WATT_PER_KELVIN = "W/K"


@dataclass(frozen=True, kw_only=True)
class HouseSensorDescription(SensorEntityDescription):
    value: Callable[[HouseRuntime], str | float | None]
    attributes: Callable[[HouseRuntime], dict[str, Any]] | None = None
    exists: Callable[[HouseRuntime], bool] = lambda _runtime: True
    """Only created when this returns True (e.g. a source sensor is configured)."""


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
    HouseSensorDescription(
        key="room_coverage",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value=lambda r: 100.0 - r.shares.unassigned_pct,
        attributes=lambda r: {
            "missing_pct": round(r.shares.unassigned_pct, 1),
            "floor_area_not_in_rooms_m2": r.floor_area_not_in_rooms_m2,
            "rooms": len(r.rooms),
        },
    ),
    HouseSensorDescription(
        key="rooms_heat_demand",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda r: _round_or_none(r.house_balance().demand_w, 0),
        attributes=lambda r: _balance_attributes(r),
    ),
    HouseSensorDescription(
        key="rooms_estimated_output",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda r: _round_or_none(r.house_balance().radiators_w, 0),
        attributes=lambda r: _balance_attributes(r),
    ),
    HouseSensorDescription(
        key="rooms_heat_from_devices",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value=lambda r: _round_or_none(r.house_balance().devices_w, 0),
        attributes=lambda r: _balance_attributes(r),
    ),
    HouseSensorDescription(
        key="flow_temperature_used",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda r: r.flow_used_c,
        attributes=lambda r: {"source": r.house.flow_temperature_entity or "heating_curve"},
        exists=lambda r: r.flow_known(),
    ),
    HouseSensorDescription(
        key="return_temperature_used",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda r: r.return_used_c,
        attributes=lambda r: {"source": r.house.return_temperature_entity},
        exists=lambda r: r.house.return_temperature_entity is not None,
    ),
    HouseSensorDescription(
        key="spread_used",
        device_class=SensorDeviceClass.TEMPERATURE_DELTA,
        native_unit_of_measurement=UnitOfTemperature.KELVIN,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value=lambda r: r.spread_used_k,
        attributes=lambda r: {
            "flow": r.house.flow_temperature_entity,
            "return": r.house.return_temperature_entity,
        },
        exists=lambda r: bool(
            r.house.flow_temperature_entity and r.house.return_temperature_entity
        ),
    ),
    HouseSensorDescription(
        key="design_day_flow",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda r: _design_day_flow(r),
        attributes=lambda r: _curve_attributes(r),
        exists=lambda r: r.flow_known(),
    ),
)
"""DIA-014: the learned heating curve, extended to the design day."""


def _balance_attributes(runtime: HouseRuntime) -> dict[str, Any]:
    """MDL-052 to MDL-054: all house sums cover the same rooms."""
    balance = runtime.house_balance()
    return {
        "rooms": balance.rooms,
        "rooms_without_estimate": list(balance.rooms_without_estimate),
    }


def _design_day_flow(runtime: HouseRuntime) -> float | None:
    curve = runtime.design_curve()
    design = runtime.house.design_outdoor_temperature_c
    if curve is None or design is None:
        return None
    return round(curve.flow_at(design), 1)


def _curve_attributes(runtime: HouseRuntime) -> dict[str, Any]:
    design = runtime.house.design_outdoor_temperature_c
    points = runtime.house.heating_curve
    if runtime.house.flow_temperature_entity is None and points is not None:
        # MDL-019: the curve entered in the house settings.
        return {
            "source": "heating_curve",
            "cold_outdoor_c": points.cold_outdoor_c,
            "cold_flow_c": points.cold_flow_c,
            "warm_outdoor_c": points.warm_outdoor_c,
            "warm_flow_c": points.warm_flow_c,
        }
    curve = runtime.heating_curve
    if curve is None:
        return {"hours": len(runtime.curve_hours)}
    return {
        "slope_k_per_k": round(curve.slope_k_per_k, 3),
        "hours": curve.hours,
        "outdoor_min_c": round(curve.outdoor_min_c, 1),
        "outdoor_max_c": round(curve.outdoor_max_c, 1),
        "confidence": curve.confidence_at(design).value if design is not None else None,
    }


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
        "since": state.reason_since.isoformat() if state.reason_since else None,
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


HEAT_FROM_DEVICES = RoomSensorDescription(
    key="heat_from_devices",
    device_class=SensorDeviceClass.POWER,
    native_unit_of_measurement=UnitOfPower.WATT,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
    value=lambda state: state.heat_from_sources_w,
    attributes=lambda state, _runtime: {
        "sources": {
            s.entity_id: state.source_factors.get(s.entity_id, s.factor_pct)
            for s in state.room.heat_sources
        },
        "factor_entities": {
            s.entity_id: s.factor_entity for s in state.room.heat_sources if s.factor_entity
        },
    },
)
"""MDL-044: only for rooms with heat sources."""


def _sizing_attributes(state: RoomState, _runtime: HouseRuntime) -> dict[str, Any]:
    result: SizingResult | None = state.sizing
    if result is None:
        return {}
    attributes: dict[str, Any] = {
        "load_pct": _round_or_none(result.load_pct, 0),
        "factor": _round_or_none(result.factor, 2),
        "confidence": result.confidence.value if result.confidence else None,
        "basis": result.basis.value,
        "cause": result.cause.value if result.cause else None,
        "design_flow_c": _round_or_none(result.design_flow_c, 1),
        "design_demand_w": _round_or_none(result.design_demand_w, 0),
        "design_output_w": _round_or_none(result.design_output_w, 0),
        "full_open_hours": result.full_open_hours,
        "faq": f"{DOCS_URL}/en/faq/radiator_sizing.md",
    }
    if result.missing:
        attributes["missing"] = list(result.missing)
    if result.reserve:
        attributes["note"] = "reserve"
    return attributes


def _round_or_none(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def _pct_or_none(value: float | None) -> int | None:
    return None if value is None else round(value * 100)


def _learning_attributes(state: RoomState, _runtime: HouseRuntime) -> dict[str, Any]:
    learned = state.learned
    if learned is None:
        return {}
    return {
        "state": learned.state.value,
        "quiet_hours": learned.hours,
        "days": learned.days,
        "night_pct": _pct_or_none(learned.night),
        "day_pct": _pct_or_none(learned.day),
        "spread_pct": learned.spread_pct,
        "faq": f"{DOCS_URL}/en/faq/learned_demand.md",
    }


LEARNED_DEMAND = RoomSensorDescription(
    key="learned_demand",
    native_unit_of_measurement=PERCENTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    value=lambda state: _pct_or_none(state.learned.factor) if state.learned else None,
    attributes=_learning_attributes,
)
"""LRN-035: only for rooms with thermostats."""


RADIATOR_SIZING = RoomSensorDescription(
    key="radiator_sizing",
    device_class=SensorDeviceClass.ENUM,
    options=[s.value for s in Sizing],
    entity_category=EntityCategory.DIAGNOSTIC,
    value=lambda state: state.sizing.sizing.value if state.sizing else None,
    attributes=_sizing_attributes,
)
"""DIA-012: only for rooms with thermostats."""


class EstimatedOutputSensor(RoomEntity, SensorEntity):
    """MDL-013: estimated heat output of the room's radiators, next to the heat demand."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, entry: ThermogeistConfigEntry, room_id: str) -> None:
        super().__init__(entry, room_id, "estimated_output")

    @property
    def native_value(self) -> float | None:
        return _round_or_none(self.runtime.estimated_output(self._room_id).output_w, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        estimate = self.runtime.estimated_output(self._room_id)
        attributes: dict[str, Any] = {
            "max_output_w": _round_or_none(estimate.max_output_w, 0),
            "radiators": {
                r.name: {
                    "output_w": _round_or_none(r.output_w, 0),
                    "max_output_w": _round_or_none(r.max_output_w, 0),
                    "valve_pct": _round_or_none(r.valve_pct, 0),
                    "valve_source": r.valve_source.value if r.valve_source else None,
                }
                for r in estimate.radiators
            },
            "valve_characteristic": "assumed",
        }
        if estimate.missing:
            attributes["missing"] = list(estimate.missing)
        return attributes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermogeistConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        HouseSensor(entry, description)
        for description in HOUSE_SENSORS
        if description.exists(entry.runtime_data)
    )
    for room_id, state in entry.runtime_data.rooms.items():
        sensors: list[SensorEntity] = [
            RoomSensor(entry, room_id, description) for description in ROOM_SENSORS
        ]
        if state.room.heat_sources:
            sensors.append(RoomSensor(entry, room_id, HEAT_FROM_DEVICES))
        if state.thermostat_ids:
            sensors.append(PlannedValveSensor(entry, room_id))
            sensors.append(EstimatedOutputSensor(entry, room_id))
            sensors.append(RoomSensor(entry, room_id, RADIATOR_SIZING))
            sensors.append(RoomSensor(entry, room_id, LEARNED_DEMAND))
        async_add_entities(sensors, config_subentry_id=room_id)
    for thermostat_id, thermostat in entry.runtime_data.thermostats.items():
        thermostat_sensors: list[SensorEntity] = [ThermostatKindSensor(entry, thermostat_id)]
        if Role.VALVE_READ in thermostat.roles or derives_valve(thermostat.roles):
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes is None:
            return None
        return self.entity_description.attributes(self.runtime)


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
            # ACT-014: whether the plan only shows (observe) or is written (control).
            "mode": "control" if self.runtime.control.is_enabled(self._room_id) else "observe",
            "strategies": sorted({t.kind.value for t in thermostats}),
            "radiator_output_w": self.room_state.rated_output_w,
            "flow_temperature_used": _rounded(self.runtime.flow_used_c),
            "return_temperature_used": _rounded(self.runtime.return_used_c),
            "spread_used": _rounded(self.runtime.spread_used_k),
        }
        sources_w = self.room_state.heat_from_sources_w
        if sources_w is not None:
            demand = self.room_state.demand_w
            attributes["heat_from_devices_w"] = round(sources_w)
            attributes["demand_covered_by_devices_pct"] = (
                round(min(100.0, 100 * sources_w / demand)) if demand else None
            )
        if plan is not None:
            attributes |= {
                "feed_forward": (
                    None
                    if self.room_state.feed_forward_missing
                    else round(plan.feed_forward_pct, 1)
                ),
                "feed_forward_missing": self.room_state.feed_forward_missing,
                "proportional": round(plan.proportional_pct, 1),
                "integral": round(plan.integral_pct, 1),
                "limits": [limit.value for limit in plan.limits],
            }
        return attributes


def _rounded(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None


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
            "strategy": self.thermostat.strategy.value,
            "profile": self.thermostat.profile_id,
            "radiator_output_w": self.thermostat.rated_output_w,
            "roles": {role.value: entity for role, entity in self.thermostat.roles.items()},
            "valve_refresh_minutes": (
                self.thermostat.valve_refresh.total_seconds() / 60
                if self.thermostat.valve_refresh
                else None
            ),
            **self.runtime.control.write_info(self._thermostat_id),
        }


class ThermostatValveSensor(ThermostatEntity, SensorEntity):
    """The thermostat's actual valve position, next to the planned one (ACT-015, ACT-016)."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: ThermogeistConfigEntry, thermostat_id: str) -> None:
        super().__init__(entry, thermostat_id, "thermostat_valve_position")

    @property
    def _sources(self) -> list[str]:
        roles = self.thermostat.roles
        if Role.VALVE_READ in roles:
            return [roles[Role.VALVE_READ]]
        return [roles[Role.VALVE_WRITE], roles[Role.VALVE_MIN], roles[Role.CLIMATE]]

    @property
    def native_value(self) -> float | None:
        return self.runtime.valve_position(self._thermostat_id)[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        roles = self.thermostat.roles
        if Role.VALVE_READ in roles:
            return {"source": "reported"}
        climate = self.hass.states.get(roles[Role.CLIMATE])
        return {
            "source": "derived",
            "hvac_action": climate.attributes.get("hvac_action") if climate else None,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(self.hass, self._sources, self._source_changed)
        )

    @callback
    def _source_changed(self, _event: Event[EventStateChangedData]) -> None:
        self.async_write_ha_state()
