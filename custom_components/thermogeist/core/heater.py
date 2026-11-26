# SPDX-License-Identifier: MIT
"""Heaters with stages: switched instead of a valve (spec ACT-060 to ACT-067, ACT-069).

A heater has 1 to N stages; a plain on/off heater is N = 1. Thermogeist knows no device: the
user's templates say which stage runs (stage sensor) and set a stage (stage setter). The room
controller plans a share of the heaters' maximum output; here it becomes time on two
neighbouring stages within a cycle.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from itertools import pairwise

from .controller import FULL_PCT
from .output import OutputEstimate, RadiatorOutput
from .radiator import RADIATOR_EXPONENT, available_output_w

# ACT-060: no common heater has more stages; keeps the dialog short.
HEATER_STAGES_MAX = 5
# ACT-062: radiators follow EN 442 with 1.3; forced convection (fan convectors) is almost
# linear (≈ 1.0). Outside 0.8-2.0 no real heater exists, so it is a typing error.
HEATER_EXPONENT_DEFAULT = RADIATOR_EXPONENT
HEATER_EXPONENT_MIN = 0.8
HEATER_EXPONENT_MAX = 2.0
# ACT-063: long enough that relay and fan do not switch every minute, short enough that the
# room temperature barely notices a cycle.
HEATER_CYCLE = timedelta(minutes=20)
HEATER_MIN_RUN = timedelta(minutes=5)
# ACT-064: a template from a power sensor needs a moment after switching on (fan start-up,
# reporting interval of the plug).
HEATER_FAULT_AFTER = timedelta(minutes=3)

FIELD_STAGES = "stages"
FIELD_STAGE_OUTPUTS = "stage_outputs"
FIELD_OFF_OUTPUT = "off_output"
FIELD_EXPONENT = "exponent"
FIELD_STAGE_SENSOR = "stage_sensor"


class EnergySource(StrEnum):
    """ACT-061: where a heater's heat comes from."""

    HEATING_CIRCUIT = "heating_circuit"
    DIRECT = "direct"


class StageSource(StrEnum):
    """ACT-065: how the current stage is known."""

    STAGE_SENSOR = "stage_sensor"
    STAGE_SETTER = "stage_setter"
    SWITCH = "switch"


@dataclass(frozen=True, slots=True)
class Heater:
    """A heater with stages assigned to a room (ACT-060)."""

    room_id: str
    name: str
    switch_entity: str
    energy_source: EnergySource
    stage_outputs_w: tuple[float, ...]
    """ACT-062: heat output per stage 1..N (heating circuit: at 75/65/20 °C)."""
    off_output_w: float = 0.0
    exponent: float = HEATER_EXPONENT_DEFAULT
    stage_sensor: str | None = None
    stage_setter: str | None = None

    @property
    def stages(self) -> int:
        return len(self.stage_outputs_w)

    def rated_w(self, stage: int) -> float:
        """Entered output of a stage; stage 0 is the output while switched off."""
        return self.off_output_w if stage == 0 else self.stage_outputs_w[stage - 1]

    def rated_by_stage(self) -> list[float]:
        return [self.rated_w(stage) for stage in range(self.stages + 1)]


def validate_heater(
    stages: int,
    outputs_w: Sequence[float],
    off_output_w: float,
    exponent: float,
    *,
    has_stage_sensor: bool,
    has_stage_setter: bool,
) -> dict[str, str]:
    """Field → error code for a heater as entered in the dialog (ACT-060, ACT-062, ACT-067)."""
    errors: dict[str, str] = {}
    if not 1 <= stages <= HEATER_STAGES_MAX:
        errors[FIELD_STAGES] = "heater_stages_range"
    elif len(outputs_w) != stages:
        errors[FIELD_STAGE_OUTPUTS] = "heater_outputs_count"
    elif not _rising([off_output_w, *outputs_w]) or off_output_w < 0:
        errors[FIELD_STAGE_OUTPUTS] = "heater_outputs_rising"
    if not HEATER_EXPONENT_MIN <= exponent <= HEATER_EXPONENT_MAX:
        errors[FIELD_EXPONENT] = "heater_exponent_range"
    if stages > 1 and not (has_stage_sensor or has_stage_setter):
        errors[FIELD_STAGE_SENSOR] = "heater_needs_stage_entity"
    return errors


def _rising(values: Sequence[float]) -> bool:
    return all(later > earlier for earlier, later in pairwise(values))


def parse_outputs(text: str) -> list[float] | None:
    """Outputs as typed in the dialog: "1300, 1700" or "1300; 1700". None if unreadable."""
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    try:
        return [float(p) for p in parts]
    except ValueError:
        return None


def available_w(
    heater: Heater,
    stage: int,
    flow_c: float | None,
    room_c: float | None,
    spread_k: float | None = None,
) -> float | None:
    """ACT-062: what a stage gives now; None for the heating circuit without temperatures."""
    rated = heater.rated_w(stage)
    if heater.energy_source is EnergySource.DIRECT:
        return rated
    if flow_c is None or room_c is None:
        return None
    return available_output_w(rated, flow_c, room_c, spread_k, heater.exponent)


def heater_feed_forward_pct(
    net_demand_w: float | None,
    heaters: Sequence[Heater],
    flow_c: float | None,
    room_c: float | None,
    spread_k: float | None = None,
) -> float | None:
    """ACT-063: share of the top stages' output the room needs, linear (no valve curve)."""
    if net_demand_w is None or not heaters:
        return None
    tops = [available_w(h, h.stages, flow_c, room_c, spread_k) for h in heaters]
    if any(top is None for top in tops):
        return None
    total = sum(top or 0.0 for top in tops)
    if total <= 0:
        return FULL_PCT
    return FULL_PCT * min(1.0, max(0.0, net_demand_w / total))


def parse_stage(value: str | None, stages: int) -> int | None:
    """ACT-066: a whole number 0..N, anything else is unknown."""
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if not number.is_integer() or not 0 <= number <= stages:
        return None
    return int(number)


def current_stage(
    heater: Heater,
    *,
    switch_on: bool | None,
    sensor_stage: int | None,
    setter_stage: int | None,
) -> tuple[int | None, StageSource]:
    """ACT-066: which stage runs now, and how that is known."""
    if heater.stage_sensor is not None:
        return sensor_stage, StageSource.STAGE_SENSOR
    if switch_on is None:
        return None, StageSource.SWITCH
    if not switch_on:
        return 0, StageSource.SWITCH
    if heater.stage_setter is not None and setter_stage:
        return setter_stage, StageSource.STAGE_SETTER
    return 1, StageSource.SWITCH


@dataclass(frozen=True, slots=True)
class StagePlan:
    """ACT-063: run ``upper`` for ``upper_share`` of the cycle, ``lower`` for the rest."""

    lower: int
    upper: int
    upper_share: float

    def planned_stage(self) -> int:
        """The stage that carries most of the cycle (for display)."""
        return self.upper if self.upper_share >= 0.5 else self.lower


OFF_PLAN = StagePlan(0, 1, 0.0)


def stage_plan(share_pct: float, heater: Heater, *, running_stage: int | None) -> StagePlan:
    """ACT-063, ACT-067: place the planned heat between two neighbouring stages.

    All stages of a heater follow the same curve, so the share between them is the same with
    entered and with available outputs; the plan therefore works without the flow temperature.
    ``running_stage`` is given when the stage cannot be set: then only off and that stage.
    """
    rated = heater.rated_by_stage()
    heat = min(1.0, max(0.0, share_pct / FULL_PCT)) * rated[heater.stages]
    if running_stage is not None:
        upper = min(heater.stages, max(1, running_stage))
        return StagePlan(0, upper, _between(heat, rated[0], rated[upper]))
    for stage in range(1, heater.stages + 1):
        if heat <= rated[stage]:
            return StagePlan(stage - 1, stage, _between(heat, rated[stage - 1], rated[stage]))
    return StagePlan(heater.stages - 1, heater.stages, 1.0)


def _between(heat: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 1.0
    return min(1.0, max(0.0, (heat - lower) / (upper - lower)))


@dataclass(slots=True)
class StageCycler:
    """ACT-063: time-proportional switching with minimum run times and carry-over."""

    cycle_start: datetime | None = None
    plan: StagePlan = OFF_PLAN
    upper_run: timedelta = timedelta(0)
    carry: timedelta = timedelta(0)
    """What earlier cycles could not run because of the minimum time (may be negative)."""

    def step(self, plan: StagePlan, now: datetime) -> int:
        """The stage to run now. A new plan applies from the next cycle."""
        if self.cycle_start is None or now - self.cycle_start >= HEATER_CYCLE:
            self._start_cycle(plan, now)
        assert self.cycle_start is not None
        if now - self.cycle_start < self.upper_run:
            return self.plan.upper
        return self.plan.lower

    def interrupt(self) -> None:
        """Window or central stop: off at once, the next plan starts a fresh cycle."""
        self.cycle_start = None
        self.plan = OFF_PLAN
        self.upper_run = timedelta(0)
        self.carry = timedelta(0)

    def _start_cycle(self, plan: StagePlan, now: datetime) -> None:
        if plan.upper_share in (0.0, 1.0):
            # Nothing to carry when the plan is all one stage; an old rest would only add a
            # surprising extra run much later.
            self.carry = timedelta(0)
        wanted = HEATER_CYCLE * plan.upper_share + self.carry
        if wanted < HEATER_MIN_RUN:
            run = timedelta(0)
        elif HEATER_CYCLE - wanted < HEATER_MIN_RUN:
            run = HEATER_CYCLE
        else:
            run = wanted
        self.carry = wanted - run
        self.cycle_start = now
        self.plan = plan
        self.upper_run = run


def heater_fault(
    *,
    on_since: datetime | None,
    stage: int | None,
    now: datetime,
    was_fault: bool,
) -> bool:
    """ACT-064: switched on for a while, but the stage sensor says nothing runs."""
    if stage is not None and stage > 0:
        return False
    if was_fault:
        return True
    return on_since is not None and stage == 0 and now - on_since >= HEATER_FAULT_AFTER


def heater_key(heater: Heater) -> str:
    """CTL-045: identifies a heater's wiring; a change makes the learned correction stale."""
    return "|".join(
        [
            "heater",
            heater.switch_entity,
            heater.energy_source.value,
            str(heater.stages),
            heater.stage_sensor or "",
            heater.stage_setter or "",
        ]
    )


@dataclass(frozen=True, slots=True)
class HeaterReading:
    """What the HA layer knows about a heater right now."""

    heater: Heater
    stage: int | None
    fault: bool = False


def estimate_heaters_output(
    readings: Sequence[HeaterReading],
    flow_c: float | None,
    room_c: float | None,
    spread_k: float | None = None,
) -> OutputEstimate:
    """MDL-013 for heaters: the available output of the running stage; 0 W during a fault."""
    results: list[RadiatorOutput] = []
    missing: list[str] = []
    for reading in readings:
        heater = reading.heater
        maximum = available_w(heater, heater.stages, flow_c, room_c, spread_k)
        if reading.fault:
            output: float | None = 0.0
        elif reading.stage is None:
            output = None
        else:
            output = available_w(heater, reading.stage, flow_c, room_c, spread_k)
        results.append(RadiatorOutput(heater.name, output, maximum, None, None, reading.stage))
    circuit = any(r.heater.energy_source is EnergySource.HEATING_CIRCUIT for r in readings)
    if circuit and flow_c is None:
        missing.append("flow_temperature")
    if circuit and room_c is None:
        missing.append("room_temperature")
    if any(r.stage is None and not r.fault for r in readings):
        missing.append("heater_stage")
    complete = bool(results) and all(r.output_w is not None for r in results)
    maxima = [r.max_output_w for r in results]
    return OutputEstimate(
        output_w=sum(r.output_w or 0.0 for r in results) if complete else None,
        max_output_w=(
            sum(m or 0.0 for m in maxima) if maxima and all(m is not None for m in maxima) else None
        ),
        radiators=tuple(results),
        missing=tuple(missing),
    )
