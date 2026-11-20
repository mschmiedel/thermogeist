# SPDX-License-Identifier: MIT
"""Room controller: feed-forward + slow PI + output shaping (spec CTL-001 to CTL-005,
CTL-030 to CTL-035).

The controller turns a target temperature into a heat demand of 0-100 %. It never reads the
clock; the caller passes the current time. Every result carries its parts so the UI can explain
why the valve would move.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

from .radiator import available_output_w

FULL_PCT = 100.0
# CTL-031: 15 % valve per kelvin of error. Calm enough for heat pumps, still noticeable.
KP_PCT_PER_K = 15.0
# CTL-032: integral time follows the room time constant, within sensible bounds.
TI_MIN_H = 2.0
TI_MAX_H = 24.0
TI_DEFAULT_H = 8.0
INTEGRAL_START_WITHOUT_FEED_FORWARD_PCT = 30.0
# CTL-032: with a feed-forward, integrate only near the target; large errors are the
# proportional part's job. Without a feed-forward the integral has to do the whole work.
INTEGRAL_BAND_K = 1.0
# CTL-033: the reported position only changes by at least this much, so rounding never makes
# the valve twitch back and forth (battery, noise).
OUTPUT_HYSTERESIS_PCT = 1.0
# CTL-037: comfort beats the minimum opening. If the room is this far above the dead band, the
# valve may close further (typical for oversized radiators, e.g. small bathrooms).
MIN_OPENING_RELAX_K = 0.5
# CTL-034: a room with a silent sensor never goes below this, whatever the profile says.
SAFETY_MIN_OPENING_PCT = 20.0
MINUTES_PER_RATE_WINDOW = 30.0
# CTL-036: heat output rises steeply right after the valve starts to open (a radiator with half
# the flow still gives most of its heat). The feed-forward inverts this typical characteristic:
# valve = opening point + (100 % - opening point) x heat fraction ^ 2. Learned later (LRN-003).
TYPICAL_OPENING_POINT_PCT = 10.0
VALVE_CHARACTERISTIC_EXPONENT = 2.0


class Limit(StrEnum):
    """Why the output differs from feed-forward + P + I."""

    STOPPED = "stopped"
    SAFETY = "safety"
    WINDOW = "window"
    SATURATED = "saturated"
    MIN_OPENING = "min_opening"
    MIN_OPENING_RELAXED = "min_opening_relaxed"
    RATE_LIMIT = "rate_limit"


@dataclass(frozen=True, slots=True)
class ControllerSettings:
    """Effective control settings of the house (CTL-014)."""

    min_opening_pct: float
    dead_band_k: float
    max_change_pct_per_30min: float


@dataclass(frozen=True, slots=True)
class ControllerInputs:
    target_c: float | None
    """None means: do not heat (central stop)."""
    room_c: float | None
    feed_forward_pct: float | None
    """None without heat load, radiator output or flow temperature."""
    time_constant_h: float | None
    safety: bool
    settings: ControllerSettings
    window_open: bool = False
    """RUL-010: close at once, and resume from the previous position afterwards."""


@dataclass(frozen=True, slots=True)
class ControllerResult:
    output_pct: float
    feed_forward_pct: float
    proportional_pct: float
    integral_pct: float
    limits: tuple[Limit, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ControllerState:
    integral_pct: float | None = None
    last_output_pct: float | None = None
    last_reported_pct: float | None = None
    last_time: datetime | None = None
    min_opening_relaxed: bool = False
    before_window_pct: float | None = None


def feed_forward_pct(
    demand_w: float | None, rated_output_w: float | None, flow_c: float | None, room_c: float | None
) -> float | None:
    """Share of the radiator's current capacity the room needs (CTL-030)."""
    if demand_w is None or not rated_output_w or flow_c is None or room_c is None:
        return None
    available = available_output_w(rated_output_w, flow_c, room_c)
    if available <= 0:
        return FULL_PCT
    heat_fraction = min(1.0, demand_w / available)
    if heat_fraction <= 0:
        return 0.0
    return TYPICAL_OPENING_POINT_PCT + (FULL_PCT - TYPICAL_OPENING_POINT_PCT) * (
        heat_fraction**VALVE_CHARACTERISTIC_EXPONENT
    )


def integral_time_h(time_constant_h: float | None) -> float:
    if time_constant_h is None:
        return TI_DEFAULT_H
    return min(TI_MAX_H, max(TI_MIN_H, time_constant_h))


def effective_error_k(target_c: float, room_c: float, dead_band_k: float) -> float:
    """Overshoot inside the dead band is ignored by the proportional part (CTL-031)."""
    error = target_c - room_c
    if error >= 0:
        return error
    return min(0.0, error + dead_band_k)


class RoomController:
    """Stateful controller of one room."""

    def __init__(self) -> None:
        self.state = ControllerState()

    def step(self, inputs: ControllerInputs, now: datetime) -> ControllerResult:
        elapsed_h = self._elapsed_h(now)
        settings = inputs.settings

        if inputs.window_open:
            if self.state.before_window_pct is None:
                self.state.before_window_pct = self.state.last_output_pct
            result = ControllerResult(
                0.0, 0.0, 0.0, self.state.integral_pct or 0.0, (Limit.WINDOW,)
            )
            self.state.last_time = now
            self.state.last_reported_pct = 0.0
            return result
        if self.state.before_window_pct is not None:
            # Window closed again: continue where we were instead of ramping up slowly.
            self.state.last_output_pct = self.state.before_window_pct
            self.state.last_reported_pct = None
            self.state.before_window_pct = None

        if inputs.target_c is None:
            result = ControllerResult(
                0.0, 0.0, 0.0, self.state.integral_pct or 0.0, (Limit.STOPPED,)
            )
        elif inputs.safety or inputs.room_c is None:
            safe = max(settings.min_opening_pct, SAFETY_MIN_OPENING_PCT)
            result = ControllerResult(
                safe, 0.0, 0.0, self.state.integral_pct or 0.0, (Limit.SAFETY,)
            )
        else:
            result = self._regulate(inputs, elapsed_h)

        # Keep the unrounded value: rounding each minute would swallow small rate-limited steps.
        self.state.last_output_pct = result.output_pct
        self.state.last_time = now
        reported = self.state.last_reported_pct
        if reported is None or abs(result.output_pct - reported) >= OUTPUT_HYSTERESIS_PCT:
            reported = float(round(result.output_pct))
        self.state.last_reported_pct = reported
        return replace(result, output_pct=reported)

    def _regulate(self, inputs: ControllerInputs, elapsed_h: float) -> ControllerResult:
        assert inputs.target_c is not None and inputs.room_c is not None
        settings = inputs.settings
        if self.state.integral_pct is None:
            self.state.integral_pct = (
                0.0
                if inputs.feed_forward_pct is not None
                else INTEGRAL_START_WITHOUT_FEED_FORWARD_PCT
            )
        raw_error = inputs.target_c - inputs.room_c
        error = effective_error_k(inputs.target_c, inputs.room_c, settings.dead_band_k)
        ff = inputs.feed_forward_pct or 0.0
        proportional = KP_PCT_PER_K * error
        integral = self.state.integral_pct
        raw = ff + proportional + integral
        limits: list[Limit] = []

        saturated_high = raw >= FULL_PCT and raw_error > 0
        too_warm = self._update_relaxed(raw_error, settings)
        floor = 0.0 if too_warm else settings.min_opening_pct
        saturated_low = raw <= floor and raw_error < 0
        if saturated_high or saturated_low:
            limits.append(Limit.SATURATED)
        elif inputs.feed_forward_pct is None or abs(raw_error) <= INTEGRAL_BAND_K:
            # The dead band only calms the proportional part; the integral still sees the true
            # error, so a lasting overshoot is removed slowly while short peaks barely matter.
            step = KP_PCT_PER_K * raw_error * elapsed_h / integral_time_h(inputs.time_constant_h)
            self.state.integral_pct = max(-FULL_PCT, min(FULL_PCT, integral + step))

        output = max(0.0, min(FULL_PCT, raw))
        if output < settings.min_opening_pct:
            if too_warm:
                limits.append(Limit.MIN_OPENING_RELAXED)
            else:
                output = settings.min_opening_pct
                limits.append(Limit.MIN_OPENING)
        output = self._rate_limited(output, settings, elapsed_h, limits)
        return ControllerResult(
            output_pct=output,
            feed_forward_pct=ff,
            proportional_pct=proportional,
            integral_pct=integral,
            limits=tuple(limits),
        )

    def _update_relaxed(self, raw_error: float, settings: ControllerSettings) -> bool:
        """Hysteresis: relax above dead band + 0.5 K, restore once back inside the dead band."""
        if raw_error < -(settings.dead_band_k + MIN_OPENING_RELAX_K):
            self.state.min_opening_relaxed = True
        elif raw_error > -settings.dead_band_k:
            self.state.min_opening_relaxed = False
        return self.state.min_opening_relaxed

    def _rate_limited(
        self,
        output: float,
        settings: ControllerSettings,
        elapsed_h: float,
        limits: list[Limit],
    ) -> float:
        last = self.state.last_output_pct
        if last is None or elapsed_h <= 0:
            return output
        max_delta = settings.max_change_pct_per_30min * elapsed_h * 60 / MINUTES_PER_RATE_WINDOW
        if abs(output - last) > max_delta:
            limits.append(Limit.RATE_LIMIT)
            return last + max_delta if output > last else last - max_delta
        return output

    def _elapsed_h(self, now: datetime) -> float:
        if self.state.last_time is None:
            return 0.0
        return max(0.0, (now - self.state.last_time).total_seconds() / 3600)
