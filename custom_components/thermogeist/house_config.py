# SPDX-License-Identifier: MIT
"""Translate between config entry data and the core house and room models."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_ABOVE,
    CONF_AREA,
    CONF_BELOW,
    CONF_CEILING_HEIGHT,
    CONF_CEILING_LOW,
    CONF_CURVE_COLD_FLOW,
    CONF_CURVE_COLD_OUTDOOR,
    CONF_CURVE_WARM_FLOW,
    CONF_CURVE_WARM_OUTDOOR,
    CONF_DESIGN_INDOOR,
    CONF_DESIGN_TEMPERATURE,
    CONF_DEVICE,
    CONF_EXTERIOR_WALLS,
    CONF_FLOOR_AREA,
    CONF_FLOW_TEMPERATURE_ENTITY,
    CONF_HEAT_LOAD,
    CONF_HEAT_SOURCES,
    CONF_HEATING_TYPE,
    CONF_KNOWN_SHARE,
    CONF_LIVING_AREA,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_PROFILE,
    CONF_RATED_OUTPUT,
    CONF_RETURN_TEMPERATURE_ENTITY,
    CONF_ROLES,
    CONF_ROOM,
    CONF_SHARE_MODE,
    CONF_SHARE_OUTSIDE,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_FACTOR,
    CONF_SOURCE_FACTOR_ENTITY,
    CONF_STRATEGY,
    CONF_TEMPERATURE_ENTITY,
    CONF_THERMOSTAT_NAME,
    CONF_THERMOSTATS,
    CONF_VALVE_MIN_INVERTED,
    CONF_VALVE_REFRESH,
    CONF_WINDOWS,
    SUBENTRY_ROOM,
)
from .core.actuator import Role, Strategy, Thermostat
from .core.house import CurvePoints, HeatingType, House
from .core.room import (
    DEFAULT_CEILING_HEIGHT_M,
    DEFAULT_DESIGN_INDOOR_C,
    DEFAULT_EXTERIOR_WALLS,
    HEAT_SOURCE_FACTOR_DEFAULT_PCT,
    Above,
    Below,
    HeatSource,
    Room,
    ShareMode,
)


def house_from_config(config: Mapping[str, Any]) -> House:
    """Build a house from flow input or stored entry data."""
    return House(
        name=str(config.get(CONF_NAME, "")),
        heating_type=HeatingType(config[CONF_HEATING_TYPE]),
        outdoor_temperature_entity=str(config.get(CONF_OUTDOOR_TEMPERATURE_ENTITY, "")),
        heat_load_kw=_optional_float(config.get(CONF_HEAT_LOAD)),
        design_outdoor_temperature_c=_optional_float(config.get(CONF_DESIGN_TEMPERATURE)),
        share_outside_pct=_optional_float(config.get(CONF_SHARE_OUTSIDE)) or 0.0,
        living_area_m2=_optional_float(config.get(CONF_LIVING_AREA)),
        flow_temperature_entity=config.get(CONF_FLOW_TEMPERATURE_ENTITY) or None,
        return_temperature_entity=config.get(CONF_RETURN_TEMPERATURE_ENTITY) or None,
        heating_curve=_curve(config),
    )


def _curve(config: Mapping[str, Any]) -> CurvePoints | None:
    """MDL-019: the heating curve points, only when all four are given."""
    values = [
        _optional_float(config.get(key))
        for key in (
            CONF_CURVE_COLD_OUTDOOR,
            CONF_CURVE_COLD_FLOW,
            CONF_CURVE_WARM_OUTDOOR,
            CONF_CURVE_WARM_FLOW,
        )
    ]
    if any(v is None for v in values):
        return None
    cold_out, cold_flow, warm_out, warm_flow = (float(v) for v in values if v is not None)
    return CurvePoints(cold_out, cold_flow, warm_out, warm_flow)


def house_from_entry(entry: ConfigEntry) -> House:
    """The effective house: stored data, overridden by later changes in the options."""
    return house_from_config({**entry.data, **entry.options})


def room_from_config(config: Mapping[str, Any]) -> Room:
    """Build a room from flow input or stored sub-entry data."""
    walls = config.get(CONF_EXTERIOR_WALLS)
    return Room(
        name=str(config.get(CONF_NAME, "")),
        temperature_entity=str(config.get(CONF_TEMPERATURE_ENTITY, "")),
        share_mode=ShareMode(config.get(CONF_SHARE_MODE, ShareMode.ESTIMATED)),
        known_share_pct=_optional_float(config.get(CONF_KNOWN_SHARE)),
        floor_area_m2=_optional_float(config.get(CONF_FLOOR_AREA)),
        ceiling_height_m=_optional_float(config.get(CONF_CEILING_HEIGHT))
        or DEFAULT_CEILING_HEIGHT_M,
        ceiling_low_m=_optional_float(config.get(CONF_CEILING_LOW)),
        exterior_walls=int(walls) if walls is not None else DEFAULT_EXTERIOR_WALLS,
        above=Above(config.get(CONF_ABOVE, Above.HEATED)),
        below=Below(config.get(CONF_BELOW, Below.HEATED)),
        design_indoor_temperature_c=_optional_float(config.get(CONF_DESIGN_INDOOR))
        or DEFAULT_DESIGN_INDOOR_C,
        window_entities=tuple(config.get(CONF_WINDOWS) or ()),
        heat_sources=tuple(
            HeatSource(
                entity_id=str(source[CONF_SOURCE_ENTITY]),
                factor_pct=float(source.get(CONF_SOURCE_FACTOR, HEAT_SOURCE_FACTOR_DEFAULT_PCT)),
                factor_entity=source.get(CONF_SOURCE_FACTOR_ENTITY) or None,
            )
            for source in config.get(CONF_HEAT_SOURCES) or ()
            if source.get(CONF_SOURCE_ENTITY)
        ),
    )


def rooms_from_entry(entry: ConfigEntry, *, exclude: str | None = None) -> dict[str, Room]:
    """All rooms of a house, keyed by sub-entry id."""
    return {
        subentry_id: room_from_config(subentry.data)
        for subentry_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_ROOM and subentry_id != exclude
    }


def thermostat_from_config(config: Mapping[str, Any], name: str) -> Thermostat:
    roles = {
        Role(role): entity_id
        for role, entity_id in (config.get(CONF_ROLES) or {}).items()
        if entity_id and role in {r.value for r in Role}
    }
    return Thermostat(
        room_id=str(config.get(CONF_ROOM, "")),
        name=name,
        roles=roles,
        rated_output_w=_optional_float(config.get(CONF_RATED_OUTPUT)),
        device_id=config.get(CONF_DEVICE) or None,
        profile_id=config.get(CONF_PROFILE) or None,
        valve_min_inverted=bool(config.get(CONF_VALVE_MIN_INVERTED, False)),
        valve_refresh=(
            timedelta(minutes=float(config[CONF_VALVE_REFRESH]))
            if config.get(CONF_VALVE_REFRESH)
            else None
        ),
        strategy=_strategy(config.get(CONF_STRATEGY)),
    )


def _strategy(value: Any) -> Strategy:
    try:
        return Strategy(value)
    except ValueError:
        return Strategy.AUTOMATIC


def thermostats_from_entry(entry: ConfigEntry) -> dict[str, Thermostat]:
    """All thermostats of a house, keyed by thermostat id; they live in their room (HAI-007)."""
    return {
        thermostat_id: thermostat_from_config(
            {**data, CONF_ROOM: room_id}, str(data.get(CONF_THERMOSTAT_NAME, thermostat_id))
        )
        for room_id, subentry in entry.subentries.items()
        if subentry.subentry_type == SUBENTRY_ROOM
        for thermostat_id, data in (subentry.data.get(CONF_THERMOSTATS) or {}).items()
    }


def migrate_thermostat_subentries(
    rooms: Mapping[str, Mapping[str, Any]], thermostats: Mapping[str, tuple[str, Mapping[str, Any]]]
) -> dict[str, dict[str, Any]]:
    """HAI-007: move thermostat sub-entries (id → title, data) into their rooms' data.

    Returns the new data of every room that changed. Thermostats of missing rooms are dropped.
    The thermostat keeps its sub-entry id as thermostat id, so entity ids and history stay.
    """
    changed: dict[str, dict[str, Any]] = {}
    for thermostat_id, (title, data) in thermostats.items():
        room_id = data.get(CONF_ROOM)
        if room_id not in rooms:
            continue
        room = changed.setdefault(room_id, dict(rooms[room_id]))
        moved = {k: v for k, v in data.items() if k != CONF_ROOM}
        room[CONF_THERMOSTATS] = {
            **(room.get(CONF_THERMOSTATS) or {}),
            thermostat_id: {**moved, CONF_THERMOSTAT_NAME: title},
        }
    return changed


def room_area_id(entry: ConfigEntry, subentry_id: str) -> str | None:
    return entry.subentries[subentry_id].data.get(CONF_AREA)


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
