# SPDX-License-Identifier: MIT
"""House description and its validation (spec MDL-001 to MDL-016, RUL-003, RUL-004)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HeatingType(StrEnum):
    """What heats the house (MDL-001). Decides the controller profile."""

    HEAT_PUMP = "heat_pump"
    BOILER = "boiler"
    DIRECT_ELECTRIC = "direct_electric"


class CentralMode(StrEnum):
    """Mode for the whole house (RUL-003)."""

    AUTO = "auto"
    STOP = "stop"
    FROST_PROTECTION = "frost_protection"


# RUL-004: common TRV frost settings are 5-8 °C; 7 °C keeps a margin for poorly insulated rooms.
FROST_PROTECTION_SETPOINT_C = 7.0

# Plausibility limits for user input. Values outside are almost certainly typos.
HEAT_LOAD_KW_MIN = 0.5
HEAT_LOAD_KW_MAX = 100.0
DESIGN_TEMP_C_MIN = -40.0
DESIGN_TEMP_C_MAX = 10.0
SHARE_PCT_MIN = 0.0
SHARE_PCT_MAX = 100.0
LIVING_AREA_M2_MIN = 10.0
LIVING_AREA_M2_MAX = 10_000.0

# Field names, shared with the HA layer so errors can be shown at the right input.
FIELD_NAME = "name"
FIELD_HEAT_LOAD = "heat_load"
FIELD_DESIGN_TEMPERATURE = "design_outdoor_temperature"
FIELD_SHARE_OUTSIDE = "share_outside"
FIELD_LIVING_AREA = "living_area"


@dataclass(frozen=True, slots=True)
class House:
    """Everything the user tells Thermogeist about the house."""

    name: str
    heating_type: HeatingType
    outdoor_temperature_entity: str
    heat_load_kw: float | None = None
    design_outdoor_temperature_c: float | None = None
    share_outside_pct: float = 0.0
    living_area_m2: float | None = None
    flow_temperature_entity: str | None = None
    """MDL-007: optional; enables the feed-forward together with radiator output."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A problem with one input field, identified by a stable code."""

    field: str
    code: str


def validate_house(house: House) -> list[ValidationIssue]:
    """Return all problems with the house description. An empty list means valid."""
    issues: list[ValidationIssue] = []
    if not house.name.strip():
        issues.append(ValidationIssue(FIELD_NAME, "name_empty"))
    _check_range(issues, FIELD_HEAT_LOAD, house.heat_load_kw, HEAT_LOAD_KW_MIN, HEAT_LOAD_KW_MAX)
    _check_range(
        issues,
        FIELD_DESIGN_TEMPERATURE,
        house.design_outdoor_temperature_c,
        DESIGN_TEMP_C_MIN,
        DESIGN_TEMP_C_MAX,
    )
    _check_range(issues, FIELD_SHARE_OUTSIDE, house.share_outside_pct, SHARE_PCT_MIN, SHARE_PCT_MAX)
    _check_range(
        issues, FIELD_LIVING_AREA, house.living_area_m2, LIVING_AREA_M2_MIN, LIVING_AREA_M2_MAX
    )
    if house.heat_load_kw is not None and house.design_outdoor_temperature_c is None:
        issues.append(ValidationIssue(FIELD_DESIGN_TEMPERATURE, "design_temperature_required"))
    return issues


def _check_range(
    issues: list[ValidationIssue],
    field: str,
    value: float | None,
    minimum: float,
    maximum: float,
) -> None:
    if value is not None and not minimum <= value <= maximum:
        issues.append(ValidationIssue(field, f"{field}_out_of_range"))
