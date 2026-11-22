# SPDX-License-Identifier: MIT
"""Roles from Zigbee2MQTT exposes, for thermostats without a profile (spec ACT-034, ACT-037).

The expose names and their meaning follow the Zigbee2MQTT device documentation, generated from
zigbee-herdsman-converters (see CREDITS.md). Only names are used, no code.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from .actuator import DeviceProfile, Kind, Role, RoleMapping, Source

AUTO_PROFILE_ID = "zigbee2mqtt_auto"
"""Not a file: marks a thermostat whose roles came from its exposes (ACT-038)."""

SETTABLE = 0b010
"""Zigbee2MQTT access bit: the value can be changed via /set."""
PERCENT = "%"
CELSIUS = "°C"

VALVE_POSITION = (
    "valve_opening_degree",
    "pi_heating_demand",
    "heating_valve_position",
    "valve_position",
    "position",
)
"""Valve position in %, settable → valve_write, read only → valve_read."""
VALVE_MINIMUM = {"valve_closing_degree": True, "idle_valve_position": False}
"""Minimum opening stored on the device; True: stored as closing degree (inverted)."""
EXTERNAL_TEMPERATURE = (
    "external_temperature_input",
    "remote_temperature",
    "external_measured_room_sensor",
    "external_temperature",
)
CHILD_LOCK = ("child_lock",)
CALIBRATION_TRIGGER = ("valve_travel_calibration", "valve_adapt_process")
CALIBRATION_STATUS = ("motor_travel_calibration_status", "valve_adapt_status")


def flatten(exposes: Iterable[Mapping[str, Any]]) -> Iterator[Mapping[str, Any]]:
    """All exposes, including the features of climate and composite exposes."""
    for expose in exposes:
        features = expose.get("features")
        if features and expose.get("type") in ("climate", "composite"):
            yield from flatten(features)
        else:
            yield expose


def _name(expose: Mapping[str, Any]) -> str:
    return str(expose.get("property") or expose.get("name") or "")


def _settable(expose: Mapping[str, Any]) -> bool:
    return bool(int(expose.get("access", 0)) & SETTABLE)


def _first(
    exposes: list[Mapping[str, Any]],
    names: Iterable[str],
    *,
    unit: str | None = None,
    settable: bool | None = None,
) -> str | None:
    """The first expose (in the order of ``names``) that fits; units must match exactly."""
    by_name = {_name(e): e for e in exposes}
    for name in names:
        expose = by_name.get(name)
        if expose is None:
            continue
        if unit is not None and expose.get("unit") != unit:
            continue
        if settable is not None and _settable(expose) != settable:
            continue
        return name
    return None


def roles_from_exposes(exposes: Iterable[Mapping[str, Any]]) -> dict[Role, RoleMapping]:
    """ACT-037: map exposes to roles by name, unit and access; unknown exposes are ignored."""
    flat = list(flatten(exposes))
    roles: dict[Role, RoleMapping] = {}
    if write := _first(flat, VALVE_POSITION, unit=PERCENT, settable=True):
        roles[Role.VALVE_WRITE] = RoleMapping(write)
    if read := _first(flat, VALVE_POSITION, unit=PERCENT, settable=False):
        roles[Role.VALVE_READ] = RoleMapping(read)  # never the write expose (ACT-036)
    if minimum := _first(flat, VALVE_MINIMUM, unit=PERCENT, settable=True):
        roles[Role.VALVE_MIN] = RoleMapping(minimum, inverted=VALVE_MINIMUM[minimum])
    if external := _first(flat, EXTERNAL_TEMPERATURE, unit=CELSIUS, settable=True):
        roles[Role.EXTERNAL_TEMPERATURE] = RoleMapping(external)
    if lock := _first(flat, CHILD_LOCK, settable=True):
        roles[Role.CHILD_LOCK] = RoleMapping(lock)
    if trigger := _first(flat, CALIBRATION_TRIGGER, settable=True):
        roles[Role.CALIBRATION_TRIGGER] = RoleMapping(trigger)
    if status := _first(flat, CALIBRATION_STATUS):
        roles[Role.CALIBRATION_STATUS] = RoleMapping(status)
    return roles


def profile_from_exposes(exposes: Iterable[Mapping[str, Any]], name: str) -> DeviceProfile | None:
    """ACT-038: an untested profile from the exposes; None if nothing useful was found."""
    roles = roles_from_exposes(exposes)
    if not roles:
        return None
    return DeviceProfile(
        profile_id=AUTO_PROFILE_ID,
        name=name,
        kind=Kind.VALVE if Role.VALVE_WRITE in roles else Kind.SETPOINT,
        manufacturers=(),
        model_ids=(),
        roles={Source.Z2M: roles},
    )
