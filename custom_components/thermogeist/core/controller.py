# SPDX-License-Identifier: MIT
"""Room controller: feed-forward + slow PI + output shaping (spec CTL-001 to CTL-005,
CTL-030 to CTL-035, CTL-040).

The controller turns a target temperature into a heat demand of 0-100 %. It never reads the
clock; the caller passes the current time. Every result carries its parts so the UI can explain
why the valve would move.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from .radiator import available_output_w

FULL_PCT = 100.0
# CTL-031: 15 % valve per kelvin of error. Calm enough for heat pumps, still noticeable.
KP_PCT_PER_K = 15.0
# CTL-032: integral time follows the room time constant, within sensible bounds.
TI_MIN_H = 2.0
TI_MAX_H = 24.0
TI_DEFAULT_H = 8.0
INTEGRAL_START_WITHOUT_FEED_FORWARD_PCT = 30.0
# CTL-032: with a feed-forward, integrate upwards only near the target; large errors are the
# proportional part's job. Without a feed-forward the integral has to do the whole work.
# Downwards (room too warm) it always integrates: a lasting overshoot means the feed-forward
# asks for too much (sun, devices, a model that overestimates the demand).
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
# CTL-040: after a longer outage the stored correction no longer fits the house.
STATE_MAX_AGE = timedelta(hours=24)
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
    HOLD_WHEN_WARM = "hold_when_warm"
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
    resume_at_once: bool = False
    """RUL-010, CTL-034: the next regular step after a window or the safe position is not
    rate-limited."""
    integral_has_start_bias: bool = False
    """True while the integral contains the start value used without feed-forward."""


def feed_forward_pct(
    demand_w: float | None,
    rated_output_w: float | None,
    flow_c: float | None,
    room_c: float | None,
    spread_k: float | None = None,
) -> float | None:
    """Share of the radiator's current capacity the room needs (CTL-030)."""
    if demand_w is None or not rated_output_w or flow_c is None or room_c is None:
        return None
    available = available_output_w(rated_output_w, flow_c, room_c, spread_k)
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

    def seed(self, output_pct: float) -> None:
        """CTL-044: start from the valve's actual position after a restart.

        Without it the first step is not rate-limited and may jump (field finding: 30 → 54 %).
        """
        if self.state.last_output_pct is None:
            self.state.last_output_pct = output_pct
            self.state.last_reported_pct = float(round(output_pct))

    def snapshot(self) -> dict[str, float | bool | None]:
        """CTL-040: what survives a restart."""
        return {
            "integral_pct": self.state.integral_pct,
            "integral_has_start_bias": self.state.integral_has_start_bias,
            "min_opening_relaxed": self.state.min_opening_relaxed,
            "output_pct": self.state.last_output_pct,
        }

    def restore(self, snapshot: Mapping[str, Any], saved_at: datetime, now: datetime) -> bool:
        """CTL-040: restore a snapshot unless it is too old. Returns whether it was used."""
        if now - saved_at > STATE_MAX_AGE:
            return False
        integral = snapshot.get("integral_pct")
        self.state.integral_pct = float(integral) if integral is not None else None
        self.state.integral_has_start_bias = bool(snapshot.get("integral_has_start_bias"))
        self.state.min_opening_relaxed = bool(snapshot.get("min_opening_relaxed"))
        # CTL-040: continue from the last plan, rate-limited from the first step (like seed).
        output = snapshot.get("output_pct")
        if output is not None:
            self.seed(float(output))
        return True

    def step(self, inputs: ControllerInputs, now: datetime) -> ControllerResult:
        elapsed_h = self._elapsed_h(now)
        settings = inputs.settings

        if inputs.window_open:
            self.state.resume_at_once = True
            result = ControllerResult(
                0.0, 0.0, 0.0, self.state.integral_pct or 0.0, (Limit.WINDOW,)
            )
            self.state.last_time = now
            self.state.last_reported_pct = 0.0
            return result
        if self.state.resume_at_once:
            # RUL-010, CTL-034: after a window or the safe position, straight to the position
            # needed now - neither is a starting point to ramp from.
            self.state.last_output_pct = None
            self.state.last_reported_pct = None
            self.state.resume_at_once = False

        if inputs.target_c is None:
            result = ControllerResult(
                0.0, 0.0, 0.0, self.state.integral_pct or 0.0, (Limit.STOPPED,)
            )
        elif not inputs.safety and inputs.room_c is None and self.state.last_output_pct is not None:
            # CTL-034: right after a restart the room temperature is not read yet; keep the last
            # plan instead of falling back to the safe position.
            held = self.state.last_reported_pct
            if held is None:
                held = float(round(self.state.last_output_pct))
            self.state.last_time = now
            return ControllerResult(held, 0.0, 0.0, self.state.integral_pct or 0.0, ())
        elif inputs.safety or inputs.room_c is None:
            self.state.resume_at_once = True
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
        self._align_integral_start(has_feed_forward=inputs.feed_forward_pct is not None)
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
        elif inputs.feed_forward_pct is None or raw_error <= INTEGRAL_BAND_K:
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
        last = self.state.last_output_pct
        if raw_error < 0 and last is not None and output > last:
            # CTL-043: a room above its target never gets more heat, whatever the feed-forward
            # says (field finding: a falling flow temperature pushed the plan up while the
            # guest bathroom was already 0.3 K too warm).
            output = last
            limits.append(Limit.HOLD_WHEN_WARM)
        output = self._rate_limited(output, settings, elapsed_h, limits)
        return ControllerResult(
            output_pct=output,
            feed_forward_pct=ff,
            proportional_pct=proportional,
            integral_pct=integral,
            limits=tuple(limits),
        )

    def _align_integral_start(self, *, has_feed_forward: bool) -> None:
        """CTL-032: the 30 % start value replaces a missing feed-forward, never adds to one.

        Seen in the field: after a restart the flow sensor came a minute late, the integral
        started at 30 % and stayed there when the feed-forward arrived, counting twice.
        """
        if self.state.integral_pct is None:
            self.state.integral_pct = (
                0.0 if has_feed_forward else INTEGRAL_START_WITHOUT_FEED_FORWARD_PCT
            )
            self.state.integral_has_start_bias = not has_feed_forward
        elif has_feed_forward and self.state.integral_has_start_bias:
            self.state.integral_pct -= INTEGRAL_START_WITHOUT_FEED_FORWARD_PCT
            self.state.integral_has_start_bias = False
        elif not has_feed_forward and not self.state.integral_has_start_bias:
            self.state.integral_pct += INTEGRAL_START_WITHOUT_FEED_FORWARD_PCT
            self.state.integral_has_start_bias = True

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
            # A seeded controller is rate-limited from its first step on.
            return 0.0 if self.state.last_output_pct is None else 1 / 60
        return max(0.0, (now - self.state.last_time).total_seconds() / 3600)
