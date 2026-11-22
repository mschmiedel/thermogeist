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
# MDL-019: heating curve points. Outdoor within the design range, flows as radiator systems use.
CURVE_OUTDOOR_C_MIN = -30.0
CURVE_OUTDOOR_C_MAX = 25.0
CURVE_FLOW_C_MIN = 20.0
CURVE_FLOW_C_MAX = 80.0

# Field names, shared with the HA layer so errors can be shown at the right input.
FIELD_NAME = "name"
FIELD_HEAT_LOAD = "heat_load"
FIELD_DESIGN_TEMPERATURE = "design_outdoor_temperature"
FIELD_SHARE_OUTSIDE = "share_outside"
FIELD_LIVING_AREA = "living_area"
FIELD_CURVE_COLD_OUTDOOR = "curve_cold_outdoor"
FIELD_CURVE_COLD_FLOW = "curve_cold_flow"
FIELD_CURVE_WARM_OUTDOOR = "curve_warm_outdoor"
FIELD_CURVE_WARM_FLOW = "curve_warm_flow"


@dataclass(frozen=True, slots=True)
class CurvePoints:
    """MDL-019: two points of the heating curve set on the heat generator."""

    cold_outdoor_c: float
    cold_flow_c: float
    warm_outdoor_c: float
    warm_flow_c: float

    def flow_at(self, outdoor_c: float) -> float:
        """Straight line between the points; flat beyond them, as heat generators do."""
        if outdoor_c <= self.cold_outdoor_c:
            return self.cold_flow_c
        if outdoor_c >= self.warm_outdoor_c:
            return self.warm_flow_c
        share = (outdoor_c - self.cold_outdoor_c) / (self.warm_outdoor_c - self.cold_outdoor_c)
        return self.cold_flow_c + share * (self.warm_flow_c - self.cold_flow_c)


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
    return_temperature_entity: str | None = None
    """MDL-019: optional; the measured spread replaces the assumed 5 K."""
    heating_curve: CurvePoints | None = None
    """MDL-019: without a flow sensor, the flow follows this curve."""


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
    if (curve := house.heating_curve) is not None:
        _validate_curve(issues, curve)
    return issues


def _validate_curve(issues: list[ValidationIssue], curve: CurvePoints) -> None:
    before = len(issues)
    for field, value in (
        (FIELD_CURVE_COLD_OUTDOOR, curve.cold_outdoor_c),
        (FIELD_CURVE_WARM_OUTDOOR, curve.warm_outdoor_c),
    ):
        _check_range(issues, field, value, CURVE_OUTDOOR_C_MIN, CURVE_OUTDOOR_C_MAX)
    for field, value in (
        (FIELD_CURVE_COLD_FLOW, curve.cold_flow_c),
        (FIELD_CURVE_WARM_FLOW, curve.warm_flow_c),
    ):
        _check_range(issues, field, value, CURVE_FLOW_C_MIN, CURVE_FLOW_C_MAX)
    if len(issues) > before:
        return
    if curve.warm_outdoor_c <= curve.cold_outdoor_c:
        issues.append(ValidationIssue(FIELD_CURVE_WARM_OUTDOOR, "curve_warm_not_above_cold"))
    elif curve.warm_flow_c > curve.cold_flow_c:
        issues.append(ValidationIssue(FIELD_CURVE_WARM_FLOW, "curve_flow_rises_when_warmer"))


def _check_range(
    issues: list[ValidationIssue],
    field: str,
    value: float | None,
    minimum: float,
    maximum: float,
) -> None:
    if value is not None and not minimum <= value <= maximum:
        issues.append(ValidationIssue(field, f"{field}_out_of_range"))
