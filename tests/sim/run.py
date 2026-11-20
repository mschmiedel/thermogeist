# SPDX-License-Identifier: MIT
"""Closed-loop run: simulated room + real controller, minute by minute (spec TST-013)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from custom_components.thermogeist.core.actuation import should_write
from custom_components.thermogeist.core.controller import (
    ControllerInputs,
    ControllerResult,
    ControllerSettings,
    RoomController,
    feed_forward_pct,
)
from custom_components.thermogeist.core.heat import current_demand_w
from custom_components.thermogeist.core.radiator import time_constant_h
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

from .room import SimRoom

START = datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
STEP = timedelta(minutes=1)

HEAT_PUMP = ControllerSettings(min_opening_pct=40.0, dead_band_k=0.5, max_change_pct_per_30min=10.0)


@dataclass
class Scenario:
    room: SimRoom
    target_c: float = 20.0
    outdoor_c: float = 0.0
    flow_c: float = 40.0
    settings: ControllerSettings = HEAT_PUMP
    knows_heat_loss: bool = True
    """Whether the controller knows H (heat load given) and the radiator output."""
    gains_w: Callable[[timedelta], float] = lambda _elapsed: 0.0


@dataclass
class Trace:
    minutes: list[float] = field(default_factory=list)
    temperatures: list[float] = field(default_factory=list)
    outputs: list[float] = field(default_factory=list)
    written: list[float] = field(default_factory=list)
    """What reached the valve after write bundling (ACT-046)."""
    results: list[ControllerResult] = field(default_factory=list)


def run(scenario: Scenario, duration: timedelta) -> Trace:
    clock = FakeTimeProvider(START)
    controller = RoomController()
    room = scenario.room
    trace = Trace()
    known_h = room.heat_loss_w_per_k if scenario.knows_heat_loss else None
    tau = time_constant_h(room.floor_area_m2, known_h)
    elapsed = timedelta(0)
    valve: float | None = None
    valve_written_at = None
    while elapsed < duration:
        demand = current_demand_w(known_h, scenario.target_c, scenario.outdoor_c)
        ff = (
            feed_forward_pct(demand, room.rated_output_w, scenario.flow_c, room.temperature_c)
            if scenario.knows_heat_loss
            else None
        )
        result = controller.step(
            ControllerInputs(
                target_c=scenario.target_c,
                room_c=room.temperature_c,
                feed_forward_pct=ff,
                time_constant_h=tau,
                safety=False,
                settings=scenario.settings,
            ),
            clock.now(),
        )
        trace.minutes.append(elapsed.total_seconds() / 60)
        trace.temperatures.append(room.temperature_c)
        trace.outputs.append(result.output_pct)
        trace.results.append(result)
        urgent = bool({"window", "stopped", "safety"} & {limit.value for limit in result.limits})
        if should_write(result.output_pct, valve, valve_written_at, clock.now(), urgent=urgent):
            valve = result.output_pct
            valve_written_at = clock.now()
        assert valve is not None
        trace.written.append(valve)
        room.step(
            valve,
            scenario.outdoor_c,
            scenario.flow_c,
            scenario.gains_w(elapsed),
            STEP.total_seconds() / 60,
        )
        clock.advance(STEP)
        elapsed += STEP
    return trace
