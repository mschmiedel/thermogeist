# SPDX-License-Identifier: MIT
"""Thermostat roles, kinds and device profiles (spec ACT-001 to ACT-033)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """What an entity of a thermostat does."""

    CLIMATE = "climate"
    VALVE_READ = "valve_read"
    VALVE_WRITE = "valve_write"
    VALVE_MIN = "valve_min"
    EXTERNAL_TEMPERATURE = "external_temperature"
    CHILD_LOCK = "child_lock"
    CALIBRATION_TRIGGER = "calibration_trigger"
    CALIBRATION_STATUS = "calibration_status"
    SETPOINT_SOURCE = "setpoint_source"


class Kind(StrEnum):
    """The two generic thermostat kinds (ACT-020, ACT-021)."""

    SETPOINT = "setpoint"
    VALVE = "valve"


class Source(StrEnum):
    """Where the device comes from; entity naming differs per source."""

    Z2M = "z2m"


Z2M_UNIQUE_ID_SUFFIX = "_zigbee2mqtt"


@dataclass(frozen=True, slots=True)
class RoleMapping:
    """How to find the entity for a role in a device of a given source."""

    expose: str
    inverted: bool = False
    """For VALVE_MIN: the device stores the closing degree (min opening = 100 - value)."""


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """A known thermostat model."""

    profile_id: str
    name: str
    kind: Kind
    manufacturers: tuple[str, ...]
    model_ids: tuple[str, ...]
    roles: Mapping[Source, Mapping[Role, RoleMapping]]
    notes: tuple[str, ...] = field(default_factory=tuple)
    control_settings: Mapping[Source, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    """ACT-042: (expose, value) pairs applied when control starts, restored when it stops."""

    def matches(self, manufacturer: str | None, model_id: str | None) -> bool:
        if not model_id:
            return False
        model_ok = model_id.casefold() in {m.casefold() for m in self.model_ids}
        maker_ok = not self.manufacturers or (
            manufacturer is not None
            and manufacturer.casefold() in {m.casefold() for m in self.manufacturers}
        )
        return model_ok and maker_ok


def parse_profile(data: Mapping[str, Any]) -> DeviceProfile:
    """Build a profile from its JSON form (see device_profiles/*.json)."""
    roles = {
        Source(source): {
            Role(role): RoleMapping(
                expose=spec["expose"], inverted=bool(spec.get("inverted", False))
            )
            for role, spec in mapping.items()
        }
        for source, mapping in data["roles"].items()
    }
    return DeviceProfile(
        profile_id=data["id"],
        name=data["name"],
        kind=Kind(data["kind"]),
        manufacturers=tuple(data["match"].get("manufacturer", ())),
        model_ids=tuple(data["match"]["model_id"]),
        roles=roles,
        notes=tuple(data.get("notes", ())),
        control_settings={
            Source(source): tuple((s["expose"], str(s["value"])) for s in settings)
            for source, settings in data.get("control_settings", {}).items()
        },
    )


def find_profile(
    profiles: Iterable[DeviceProfile], manufacturer: str | None, model_id: str | None
) -> DeviceProfile | None:
    return next((p for p in profiles if p.matches(manufacturer, model_id)), None)


@dataclass(frozen=True, slots=True)
class DeviceEntity:
    """An entity of the device being assigned, as the HA layer sees it."""

    entity_id: str
    unique_id: str
    domain: str


def resolve_roles(
    entities: Iterable[DeviceEntity],
    profile: DeviceProfile | None,
    source: Source = Source.Z2M,
) -> dict[Role, str]:
    """Map roles to entity ids. The climate role is found by domain (ACT-032)."""
    entities = list(entities)
    resolved: dict[Role, str] = {}
    climate = next((e for e in entities if e.domain == "climate"), None)
    if climate is not None:
        resolved[Role.CLIMATE] = climate.entity_id
    if profile is None:
        return resolved
    for role, mapping in profile.roles.get(source, {}).items():
        marker = f"_{mapping.expose}{Z2M_UNIQUE_ID_SUFFIX}"
        match = next((e for e in entities if e.unique_id.endswith(marker)), None)
        if match is not None:
            resolved[role] = match.entity_id
    return resolved


@dataclass(frozen=True, slots=True)
class Thermostat:
    """A thermostat assigned to a room (HAI-006)."""

    room_id: str
    name: str
    roles: Mapping[Role, str]
    device_id: str | None = None
    rated_output_w: float | None = None
    """MDL-006: radiator rated output at 75/65/20 °C."""
    profile_id: str | None = None
    valve_min_inverted: bool = False

    @property
    def kind(self) -> Kind:
        return kind_for(self.roles)


def kind_for(roles: Mapping[Role, str]) -> Kind:
    """Valve-based as soon as the valve can be written (ACT-021)."""
    return Kind.VALVE if Role.VALVE_WRITE in roles else Kind.SETPOINT


@dataclass(frozen=True, slots=True)
class EntityFacts:
    """What the dialog knows about an entity chosen for a role."""

    state: str | None
    unit: str | None = None
    device_class: str | None = None
    options: tuple[str, ...] = ()


PERCENT_ROLES = frozenset({Role.VALVE_READ, Role.VALVE_WRITE, Role.VALVE_MIN})
TEMPERATURE_UNITS = frozenset({"°C", "°F", "K"})
SETPOINT_SOURCE_VALUES = frozenset({"manual", "schedule", "externally"})


def check_role(role: Role, facts: EntityFacts) -> str | None:
    """Plausibility check for a role assignment (ACT-035). Returns an error code or None."""
    if role in PERCENT_ROLES and facts.unit != "%":
        return "role_needs_percent"
    if role is Role.EXTERNAL_TEMPERATURE and not (
        facts.unit in TEMPERATURE_UNITS or facts.device_class == "temperature"
    ):
        return "role_needs_temperature"
    if role is Role.SETPOINT_SOURCE:
        values = set(facts.options) | ({facts.state} if facts.state else set())
        if not values & SETPOINT_SOURCE_VALUES:
            return "role_needs_setpoint_source"
    return None
