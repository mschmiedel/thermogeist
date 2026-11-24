# SPDX-License-Identifier: MIT
"""Models of thermostats that regulate themselves, fitted to field data (spec TST-012).

The setpoint strategy (ACT-050 to ACT-055) leaves the valve to the device's own controller. These
models reproduce how two real devices did that, so the setpoint path can be tested without the
hardware. Their parameters were fitted to the one-day recordings in ``tests/fixtures/devices/``;
``tests/core/test_device_models.py`` checks that they still reproduce them.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures" / "devices"

# Bosch Radiator Thermostat II (BTH-RA): integrating controller on its (external) temperature.
BTH_RA_OPEN_PCT_PER_K_MIN = 2.9
"""Below the setpoint the valve opens by this much per kelvin and minute."""
BTH_RA_CLOSE_PCT_PER_K_MIN = 7.5
"""Above the setpoint it closes faster: about 2.5 times the opening rate."""
BTH_RA_PROPORTIONAL_PCT_PER_K = 5.0
"""A small direct reaction to a change of the error."""

# Bosch Smart Home Radiator Thermostat (first generation): proportional band with a floor and no
# integral part within a day; the valve at zero error moved between days (39 % and 52 % on the
# two recorded days), so it is a parameter of the model.
SHC_BASE_PCT = 45.0
"""Valve at zero error; between the two recorded days."""
SHC_PCT_PER_K = 30.0
SHC_FLOOR_PCT = 23.0
"""It never closed further outside its window function, even 1.6 K above the setpoint."""
SHC_MIN_CHANGE_PCT = 10.0
"""Smaller corrections are not carried out."""
SHC_UPDATE_MINUTES = 20
"""It re-evaluates at most this often."""
SHC_WINDOW_DROP_K = 1.0
"""Own window detection: its temperature falls this much between two samples."""
SHC_WINDOW_MINUTES = 10


@dataclass
class BthRaModel:
    """Valve of a Bosch BTH-RA regulating itself on the temperature it is given."""

    valve_pct: float = 0.0
    _last_error_k: float | None = None

    def step(self, minutes: float, setpoint_c: float, device_c: float) -> float:
        error = setpoint_c - device_c
        rate = BTH_RA_OPEN_PCT_PER_K_MIN if error > 0 else BTH_RA_CLOSE_PCT_PER_K_MIN
        change = rate * error * minutes
        if self._last_error_k is not None:
            change += BTH_RA_PROPORTIONAL_PCT_PER_K * (error - self._last_error_k)
        self._last_error_k = error
        self.valve_pct = min(100.0, max(0.0, self.valve_pct + change))
        return self.valve_pct


@dataclass
class ShcModel:
    """Valve of a Bosch Smart Home thermostat (first generation) regulating on its own sensor."""

    valve_pct: float = SHC_BASE_PCT
    base_pct: float = SHC_BASE_PCT
    _elapsed_min: float = 0.0
    _last_update_min: float = 0.0
    _last_device_c: float | None = None
    _window_until_min: float = -1.0
    _samples: list[tuple[float, float]] = field(default_factory=list)

    def step(self, minutes: float, setpoint_c: float, device_c: float) -> float:
        self._elapsed_min += minutes
        now = self._elapsed_min
        if self._window_drop(device_c):
            self.valve_pct = 0.0
            self._window_until_min = now + SHC_WINDOW_MINUTES
        elif now >= self._window_until_min and now - self._last_update_min >= SHC_UPDATE_MINUTES:
            band = self.base_pct + SHC_PCT_PER_K * (setpoint_c - device_c)
            wanted = min(100.0, max(SHC_FLOOR_PCT, band))
            if abs(wanted - self.valve_pct) >= SHC_MIN_CHANGE_PCT:
                self.valve_pct = wanted
            self._last_update_min = now
        return self.valve_pct

    def align(self, valve_pct: float, error_k: float) -> None:
        """Start from a recorded state: the valve shown at the given error."""
        self.valve_pct = valve_pct
        self.base_pct = valve_pct - SHC_PCT_PER_K * error_k

    def _window_drop(self, device_c: float) -> bool:
        """A drop within 10 minutes, as the device's own window function sees it."""
        now = self._elapsed_min
        self._samples = [(t, c) for t, c in self._samples if now - t <= SHC_WINDOW_MINUTES]
        dropped = any(c - device_c >= SHC_WINDOW_DROP_K for _, c in self._samples)
        self._samples.append((now, device_c))
        return dropped


@dataclass(frozen=True, slots=True)
class Sample:
    minute: float
    setpoint_c: float
    device_c: float
    valve_pct: float


def load_recording(name: str) -> list[Sample]:
    """A recorded day: setpoint, device temperature and reported valve position."""
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        rows = csv.DictReader(line for line in handle if not line.startswith("#"))
        return [
            Sample(
                float(r["minute"]),
                float(r["setpoint_c"]),
                float(r["device_c"]),
                float(r["valve_pct"]),
            )
            for r in rows
        ]


def replay_error_pct(model: BthRaModel | ShcModel, recording: list[Sample]) -> float:
    """Mean absolute difference between the model's valve and the recorded one."""
    first = recording[0]
    if isinstance(model, ShcModel):
        model.align(first.valve_pct, first.setpoint_c - first.device_c)
    else:
        model.valve_pct = first.valve_pct
    errors = [0.0]
    for previous, sample in pairwise(recording):
        minutes = sample.minute - previous.minute
        valve = model.step(minutes, sample.setpoint_c, sample.device_c)
        errors.append(abs(valve - sample.valve_pct))
    return sum(errors) / len(errors)
