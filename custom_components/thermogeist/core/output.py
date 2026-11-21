# SPDX-License-Identifier: MIT
"""Estimated heat output of a room's radiators right now (spec MDL-013)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .controller import FULL_PCT, TYPICAL_OPENING_POINT_PCT, VALVE_CHARACTERISTIC_EXPONENT
from .radiator import available_output_w


class ValveSource(StrEnum):
    REPORTED = "reported"
    """The thermostat reports its valve position."""
    DERIVED = "derived"
    """From the device's opening and closing positions and whether it heats (ACT-016)."""
    PLANNED = "planned"
    """Thermogeist sets the valve itself; the planned position is what the valve does."""


@dataclass(frozen=True, slots=True)
class RadiatorInput:
    name: str
    rated_output_w: float | None
    valve_pct: float | None
    valve_source: ValveSource | None


@dataclass(frozen=True, slots=True)
class RadiatorOutput:
    name: str
    output_w: float | None
    max_output_w: float | None
    valve_pct: float | None
    valve_source: ValveSource | None


@dataclass(frozen=True, slots=True)
class OutputEstimate:
    output_w: float | None
    """None as soon as one radiator cannot be estimated (see ``missing``)."""
    max_output_w: float | None
    """All radiators fully open."""
    radiators: tuple[RadiatorOutput, ...] = ()
    missing: tuple[str, ...] = field(default_factory=tuple)


def output_at_valve_w(valve_pct: float, available_w: float) -> float:
    """Inverse of the feed-forward characteristic (CTL-036).

    Below the opening point no water flows; above it the output rises steeply, so a valve at
    half its range already gives most of the heat.
    """
    if available_w <= 0 or valve_pct <= TYPICAL_OPENING_POINT_PCT:
        return 0.0
    share = (min(FULL_PCT, valve_pct) - TYPICAL_OPENING_POINT_PCT) / (
        FULL_PCT - TYPICAL_OPENING_POINT_PCT
    )
    return available_w * share ** (1 / VALVE_CHARACTERISTIC_EXPONENT)


def estimate_room_output(
    radiators: list[RadiatorInput],
    flow_c: float | None,
    room_c: float | None,
    spread_k: float | None,
) -> OutputEstimate:
    """MDL-013: what the radiators give now, from rated output, temperatures and valve."""
    missing: list[str] = []
    if flow_c is None:
        missing.append("flow_temperature")
    if room_c is None:
        missing.append("room_temperature")
    results: list[RadiatorOutput] = []
    for radiator in radiators:
        available = None
        if radiator.rated_output_w and flow_c is not None and room_c is not None:
            available = available_output_w(radiator.rated_output_w, flow_c, room_c, spread_k)
        output = None
        if available is not None and radiator.valve_pct is not None:
            output = output_at_valve_w(radiator.valve_pct, available)
        results.append(
            RadiatorOutput(
                radiator.name, output, available, radiator.valve_pct, radiator.valve_source
            )
        )
    if any(not r.rated_output_w for r in radiators):
        missing.append("radiator_output")
    if any(r.valve_pct is None for r in radiators):
        missing.append("valve_position")
    complete = bool(results) and not missing
    maxima = [r.max_output_w for r in results]
    return OutputEstimate(
        output_w=sum(r.output_w or 0.0 for r in results) if complete else None,
        max_output_w=(
            sum(m for m in maxima if m is not None)
            if maxima and all(m is not None for m in maxima)
            else None
        ),
        radiators=tuple(results),
        missing=tuple(missing),
    )


@dataclass(frozen=True, slots=True)
class RoomBalanceInput:
    name: str
    demand_w: float | None
    radiators_w: float | None
    """None when the radiators cannot be estimated (or the room has none)."""
    devices_w: float | None


@dataclass(frozen=True, slots=True)
class HouseBalance:
    demand_w: float | None
    radiators_w: float | None
    devices_w: float | None
    rooms: int
    rooms_without_estimate: tuple[str, ...]


def house_balance(rooms: list[RoomBalanceInput]) -> HouseBalance:
    """MDL-052 to MDL-054: what the rooms need and get right now, over the same rooms."""
    counted = [r for r in rooms if r.radiators_w is not None]
    demands = [r.demand_w for r in counted if r.demand_w is not None]
    return HouseBalance(
        demand_w=sum(demands) if demands else None,
        radiators_w=sum(r.radiators_w or 0.0 for r in counted) if counted else None,
        devices_w=sum(r.devices_w or 0.0 for r in counted) if counted else None,
        rooms=len(counted),
        rooms_without_estimate=tuple(r.name for r in rooms if r.radiators_w is None),
    )
