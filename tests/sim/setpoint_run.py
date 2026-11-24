# SPDX-License-Identifier: MIT
"""Closed loop for the setpoint strategy: room + device model + Thermogeist's setpoint logic.

Thermogeist decides the device setpoint (ACT-051 to ACT-053) the way ``control.py`` does, the
device model moves the valve itself (TST-012), the room simulator heats (TST-010).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from custom_components.thermogeist.core.setpoint import device_setpoint_c, should_write_setpoint
from custom_components.thermogeist.core.smoothing import MovingAverage
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

from .devices import BthRaModel, ShcModel
from .room import SimRoom
from .run import START, STEP

OFFSET_WINDOW = timedelta(minutes=30)
"""ACT-052: device temperature minus room temperature, averaged over 30 minutes."""
SENSOR_RISE_AT_FULL_FLOW_K = 0.4
"""A sensor in the thermostat reads warmer than the room while the radiator heats; the
recorded dining room showed 0.1-0.3 K at its usual valve positions."""


@dataclass
class SetpointScenario:
    room: SimRoom
    device: BthRaModel | ShcModel
    external_input: bool
    """The device regulates on the room temperature (BTH-RA remote temperature, ACT-051)."""
    target_c: float = 20.5
    outdoor_c: float = 0.0
    flow_c: float = 40.0


@dataclass
class SetpointTrace:
    temperatures: list[float] = field(default_factory=list)
    valves: list[float] = field(default_factory=list)
    setpoints: list[float] = field(default_factory=list)
    writes: int = 0


def run_setpoint(scenario: SetpointScenario, duration: timedelta) -> SetpointTrace:
    clock = FakeTimeProvider(START)
    room, device = scenario.room, scenario.device
    offset = MovingAverage(OFFSET_WINDOW)
    trace = SetpointTrace()
    sent: float | None = None
    sent_at = None
    valve = device.valve_pct
    elapsed = timedelta(0)
    minutes = STEP.total_seconds() / 60
    while elapsed < duration:
        now = clock.now()
        device_c = (
            room.temperature_c
            if scenario.external_input
            else room.temperature_c + SENSOR_RISE_AT_FULL_FLOW_K * room.valve_fraction(valve)
        )
        offset.add(now, device_c - room.temperature_c)
        average = offset.value(now)
        desired = device_setpoint_c(
            scenario.target_c,
            room.temperature_c,
            None if average is None else room.temperature_c + average,
            external_input=scenario.external_input,
        )
        if should_write_setpoint(desired, sent, sent_at, now):
            sent, sent_at = desired, now
            trace.writes += 1
        assert sent is not None
        valve = device.step(minutes, sent, device_c)
        trace.temperatures.append(room.temperature_c)
        trace.valves.append(valve)
        trace.setpoints.append(sent)
        room.step(valve, scenario.outdoor_c, scenario.flow_c, 0.0, minutes)
        clock.advance(STEP)
        elapsed += STEP
    return trace
