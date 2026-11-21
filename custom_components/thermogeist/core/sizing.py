# SPDX-License-Identifier: MIT
"""Radiator sizing per room and the learned heating curve (spec MDL-015, DIA-001 to DIA-015)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from statistics import median

from .radiator import available_output_w

# DIA-001 to DIA-004: load on the design day as a share of the radiator output.
HEAVILY_OVERSIZED_BELOW_PCT = 30.0
RIGHT_SIZE_UP_TO_PCT = 90.0
TIGHT_UP_TO_PCT = 100.0

# DIA-014: learned heating curve.
HEATING_RUNNING_MARGIN_K = 5.0
"""An hour counts for the curve only if the flow was this far above the rooms: heating ran."""
CURVE_HISTORY = timedelta(days=60)
CURVE_MIN_HOURS = 48
CURVE_MIN_OUTDOOR_SPAN_K = 5.0
CONFIDENCE_HIGH_UP_TO_K = 5.0
CONFIDENCE_MEDIUM_UP_TO_K = 15.0

# DIA-015: operation check.
WIDE_OPEN_PCT = 95.0
BELOW_TARGET_K = 0.5
COLD_OUTDOOR_BELOW_C = 5.0
HOUR_SHARE_REQUIRED = 0.9
FULL_OPEN_WINDOW = timedelta(days=7)
FULL_OPEN_HOURS_FOR_UNDERSIZED = 6

# DIA-011: a house-level hint needs more than a single room.
ALL_OVERSIZED_MIN_ROOMS = 2


class Sizing(StrEnum):
    """DIA-001 to DIA-005."""

    HEAVILY_OVERSIZED = "heavily_oversized"
    RIGHT_SIZE = "right_size"
    TIGHT = "tight"
    UNDERSIZED = "undersized"
    NOT_ASSESSABLE = "not_assessable"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Basis(StrEnum):
    STATIC = "static"
    OPERATION = "operation"


class Cause(StrEnum):
    RADIATOR_SMALL = "radiator_small"
    INPUT_OR_HYDRAULICS = "input_or_hydraulics"
    RADIATOR_LARGE = "radiator_large"
    FLOW_HIGH = "flow_high"


# ----- heating curve (DIA-014) ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CurveHour:
    """One hour while heating ran: mean outdoor and median flow temperature."""

    hour: datetime
    outdoor_c: float
    flow_c: float


@dataclass(frozen=True, slots=True)
class HeatingCurve:
    intercept_c: float
    slope_k_per_k: float
    hours: int
    outdoor_min_c: float
    outdoor_max_c: float

    def flow_at(self, outdoor_c: float) -> float:
        return self.intercept_c + self.slope_k_per_k * outdoor_c

    def confidence_at(self, outdoor_c: float) -> Confidence:
        """How far the line is extended below the coldest hour seen."""
        distance = self.outdoor_min_c - outdoor_c
        if distance <= CONFIDENCE_HIGH_UP_TO_K:
            return Confidence.HIGH
        if distance <= CONFIDENCE_MEDIUM_UP_TO_K:
            return Confidence.MEDIUM
        return Confidence.LOW


def fit_heating_curve(hours: Sequence[CurveHour]) -> HeatingCurve | None:
    """Least-squares line flow = a + b · outdoor; None until it is trustworthy (DIA-014)."""
    if len(hours) < CURVE_MIN_HOURS:
        return None
    xs = [h.outdoor_c for h in hours]
    ys = [h.flow_c for h in hours]
    if max(xs) - min(xs) < CURVE_MIN_OUTDOOR_SPAN_K:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / sxx
    if slope >= 0:
        # A heating curve falls with rising outdoor temperature; anything else is noise.
        return None
    return HeatingCurve(
        intercept_c=mean_y - slope * mean_x,
        slope_k_per_k=slope,
        hours=len(hours),
        outdoor_min_c=min(xs),
        outdoor_max_c=max(xs),
    )


def heating_ran(flow_median_c: float, mean_room_c: float | None) -> bool:
    if mean_room_c is None:
        return False
    return flow_median_c >= mean_room_c + HEATING_RUNNING_MARGIN_K


def recent_hours(hours: Iterable[CurveHour], now: datetime) -> list[CurveHour]:
    return [h for h in hours if now - h.hour <= CURVE_HISTORY]


@dataclass(slots=True)
class HourCollector:
    """Collects minute samples and closes one hour at a time; time comes from the caller."""

    hour: datetime | None = None
    outdoor: list[float] = field(default_factory=list)
    flow: list[float] = field(default_factory=list)
    rooms: list[float] = field(default_factory=list)
    flags: dict[str, list[bool]] = field(default_factory=dict)

    def add(
        self,
        now: datetime,
        outdoor_c: float | None,
        flow_c: float | None,
        mean_room_c: float | None,
        full_open: dict[str, bool],
    ) -> HourResult | None:
        """Add one sample; returns the finished previous hour when a new hour begins."""
        hour = now.replace(minute=0, second=0, microsecond=0)
        finished = self._close() if self.hour is not None and hour != self.hour else None
        if self.hour != hour:
            self.hour = hour
            self.outdoor, self.flow, self.rooms, self.flags = [], [], [], {}
        if outdoor_c is not None:
            self.outdoor.append(outdoor_c)
        if flow_c is not None:
            self.flow.append(flow_c)
        if mean_room_c is not None:
            self.rooms.append(mean_room_c)
        for room_id, flag in full_open.items():
            self.flags.setdefault(room_id, []).append(flag)
        return finished

    def _close(self) -> HourResult:
        assert self.hour is not None
        curve_hour = None
        if self.outdoor and self.flow:
            flow = median(self.flow)
            room = sum(self.rooms) / len(self.rooms) if self.rooms else None
            if heating_ran(flow, room):
                curve_hour = CurveHour(self.hour, sum(self.outdoor) / len(self.outdoor), flow)
        full_open_rooms = {
            room_id
            for room_id, flags in self.flags.items()
            if flags and sum(flags) / len(flags) >= HOUR_SHARE_REQUIRED
        }
        return HourResult(self.hour, curve_hour, full_open_rooms)


@dataclass(frozen=True, slots=True)
class HourResult:
    hour: datetime
    curve_hour: CurveHour | None
    full_open_rooms: set[str]


# ----- operation check (DIA-015) --------------------------------------------------------------


def fully_open_in_cold(
    valve_pct: float | None,
    room_c: float | None,
    target_c: float | None,
    outdoor_c: float | None,
    reason_is_setpoint: bool,
) -> bool:
    """One minute of 'valve wide open, cold outside, room clearly below target'."""
    if valve_pct is None or room_c is None or target_c is None or outdoor_c is None:
        return False
    return (
        reason_is_setpoint
        and valve_pct >= WIDE_OPEN_PCT
        and room_c < target_c - BELOW_TARGET_K
        and outdoor_c < COLD_OUTDOOR_BELOW_C
    )


def full_open_hours_in_window(hours: Iterable[datetime], now: datetime) -> list[datetime]:
    return [h for h in hours if now - h <= FULL_OPEN_WINDOW]


# ----- assessment (DIA-001 to DIA-005, DIA-010, DIA-012) ---------------------------------------


@dataclass(frozen=True, slots=True)
class SizingInputs:
    heat_loss_w_per_k: float | None
    setpoint_c: float
    design_outdoor_c: float | None
    rated_output_w: float | None
    has_flow_sensor: bool
    curve: HeatingCurve | None
    spread_k: float | None
    full_open_hours: int
    heat_pump: bool


@dataclass(frozen=True, slots=True)
class SizingResult:
    sizing: Sizing
    basis: Basis = Basis.STATIC
    load_pct: float | None = None
    factor: float | None = None
    confidence: Confidence | None = None
    cause: Cause | None = None
    design_flow_c: float | None = None
    design_demand_w: float | None = None
    design_output_w: float | None = None
    full_open_hours: int = 0
    missing: tuple[str, ...] = ()
    reserve: bool = False
    """DIA-010: heavily oversized with a heat pump is a reserve, not a fault."""


def classify(load_pct: float) -> Sizing:
    if load_pct < HEAVILY_OVERSIZED_BELOW_PCT:
        return Sizing.HEAVILY_OVERSIZED
    if load_pct <= RIGHT_SIZE_UP_TO_PCT:
        return Sizing.RIGHT_SIZE
    if load_pct <= TIGHT_UP_TO_PCT:
        return Sizing.TIGHT
    return Sizing.UNDERSIZED


def _missing(inputs: SizingInputs) -> tuple[str, ...]:
    checks = (
        ("heat_load", inputs.heat_loss_w_per_k is not None and inputs.design_outdoor_c is not None),
        ("radiator_output", bool(inputs.rated_output_w)),
        ("flow_temperature", inputs.has_flow_sensor),
        ("heating_curve", inputs.curve is not None or not inputs.has_flow_sensor),
    )
    return tuple(name for name, ok in checks if not ok)


def assess(inputs: SizingInputs) -> SizingResult:
    """Static result, overruled by the operation check when that says undersized."""
    operation = inputs.full_open_hours >= FULL_OPEN_HOURS_FOR_UNDERSIZED
    missing = _missing(inputs)
    if missing:
        if operation:
            return SizingResult(
                Sizing.UNDERSIZED,
                basis=Basis.OPERATION,
                cause=Cause.INPUT_OR_HYDRAULICS,
                full_open_hours=inputs.full_open_hours,
                missing=missing,
            )
        return SizingResult(
            Sizing.NOT_ASSESSABLE, full_open_hours=inputs.full_open_hours, missing=missing
        )
    assert inputs.heat_loss_w_per_k is not None and inputs.design_outdoor_c is not None
    assert inputs.rated_output_w is not None and inputs.curve is not None
    flow = inputs.curve.flow_at(inputs.design_outdoor_c)
    demand = max(0.0, inputs.heat_loss_w_per_k * (inputs.setpoint_c - inputs.design_outdoor_c))
    output = available_output_w(inputs.rated_output_w, flow, inputs.setpoint_c, inputs.spread_k)
    load_pct = demand / output * 100 if output > 0 else float("inf")
    static = classify(load_pct)
    sizing, basis = static, Basis.STATIC
    if operation and static is not Sizing.UNDERSIZED:
        sizing, basis = Sizing.UNDERSIZED, Basis.OPERATION
    cause = None
    if sizing is Sizing.UNDERSIZED:
        cause = Cause.RADIATOR_SMALL if static is Sizing.UNDERSIZED else Cause.INPUT_OR_HYDRAULICS
    elif sizing is Sizing.HEAVILY_OVERSIZED:
        cause = Cause.RADIATOR_LARGE
    return SizingResult(
        sizing,
        basis=basis,
        load_pct=load_pct if output > 0 else None,
        factor=output / demand if demand > 0 else None,
        confidence=inputs.curve.confidence_at(inputs.design_outdoor_c),
        cause=cause,
        design_flow_c=flow,
        design_demand_w=demand,
        design_output_w=output,
        full_open_hours=inputs.full_open_hours,
        reserve=sizing is Sizing.HEAVILY_OVERSIZED and inputs.heat_pump,
    )


def all_heavily_oversized(results: Iterable[SizingResult]) -> bool:
    """DIA-011: every assessable room heavily oversized, and at least two of them."""
    assessable = [r for r in results if r.sizing is not Sizing.NOT_ASSESSABLE]
    return len(assessable) >= ALL_OVERSIZED_MIN_ROOMS and all(
        r.sizing is Sizing.HEAVILY_OVERSIZED for r in assessable
    )


def with_house_cause(result: SizingResult) -> SizingResult:
    """DIA-011: when all rooms are heavily oversized, the flow is the likely cause."""
    if result.sizing is not Sizing.HEAVILY_OVERSIZED:
        return result
    return replace(result, cause=Cause.FLOW_HIGH)
