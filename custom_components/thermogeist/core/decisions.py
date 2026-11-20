# SPDX-License-Identifier: MIT
"""The central decision point and reason catalogue (ARC-003, RSN-001, RSN-002, RUL-013 to RUL-015).

Every decision about what a room aims for is made here and carries a reason code. Nothing
changes silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from .house import FROST_PROTECTION_SETPOINT_C, CentralMode
from .time_provider import TimeProvider


class Severity(StrEnum):
    INFO = "info"
    NOTICE = "notice"
    SAFETY = "safety"


class ReasonCode(StrEnum):
    """Stable reason codes. Each one has en/de texts and an FAQ entry (RSN-005)."""

    SETPOINT = "setpoint"
    CENTRAL_STOP = "central_stop"
    FROST_PROTECTION = "frost_protection"
    SAFETY_SENSOR_STALE = "safety_sensor_stale"
    WINDOW_OPEN = "window_open"
    STARTUP_HOLD = "startup_hold"
    DEVICE_OVERRIDES_VALVE = "device_overrides_valve"


CATALOGUE: dict[ReasonCode, Severity] = {
    ReasonCode.SETPOINT: Severity.INFO,
    ReasonCode.CENTRAL_STOP: Severity.NOTICE,
    ReasonCode.FROST_PROTECTION: Severity.NOTICE,
    ReasonCode.SAFETY_SENSOR_STALE: Severity.SAFETY,
    ReasonCode.WINDOW_OPEN: Severity.NOTICE,
    ReasonCode.STARTUP_HOLD: Severity.INFO,
    # Thermostat-level: reported in the logbook and as a repair issue, not as a room reason.
    ReasonCode.DEVICE_OVERRIDES_VALVE: Severity.SAFETY,
}

# RUL-013: a room temperature older than this is not trusted. Zigbee sensors usually report at
# least every few minutes; an hour of silence means a dead battery or lost connection.
SENSOR_STALE_AFTER = timedelta(minutes=60)
# RUL-014: a window counts as open after 30 s, so a quick airing of a few seconds is ignored.
WINDOW_OPEN_AFTER = timedelta(seconds=30)
# RUL-014: heating resumes only after all contacts were closed for 10 s; switching from fully
# open to tilted passes through "closed" for a moment.
WINDOW_RESUME_AFTER = timedelta(seconds=10)
WINDOW_DELAY_MAX = timedelta(seconds=600)
# RUL-015: the frost guard ends 1 K above the frost setpoint, so it does not toggle every minute.
FROST_GUARD_HYSTERESIS_K = 1.0


@dataclass(frozen=True, slots=True)
class RoomInputs:
    """What the decision for one room depends on."""

    user_setpoint_c: float
    central_mode: CentralMode
    temperature_valid_since: datetime | None
    """Last time the room temperature sensor reported a valid value."""
    window_open_since: datetime | None = None
    """Since when a window contact of the room is open, None if all are closed."""
    startup_hold: bool = False
    """ACT-045: Home Assistant started less than 90 s ago; nothing is written yet."""
    window_closed_since: datetime | None = None
    """Since when all window contacts of the room are closed, None while one is open."""
    window_was_active: bool = False
    """The previous decision was ``window_open`` (RUL-014: resume only after the delay)."""
    window_open_after: timedelta = WINDOW_OPEN_AFTER
    window_resume_after: timedelta = WINDOW_RESUME_AFTER
    room_temperature_c: float | None = None
    frost_guard_was_active: bool = False
    """RUL-015: hysteresis state of the frost guard from the previous decision."""


@dataclass(frozen=True, slots=True)
class Decision:
    """What the room aims for, and why."""

    code: ReasonCode
    target_setpoint_c: float | None
    """None means: do not heat."""
    timestamp: datetime
    params: dict[str, float | str] = field(default_factory=dict)

    @property
    def severity(self) -> Severity:
        return CATALOGUE[self.code]


def decide_room(inputs: RoomInputs, clock: TimeProvider) -> Decision:
    """Apply the fixed precedence (RUL-030): safety, central mode, window, user setpoint."""
    now = clock.now()
    age = now - inputs.temperature_valid_since if inputs.temperature_valid_since else None
    if age is None or age >= SENSOR_STALE_AFTER:
        params: dict[str, float | str] = {
            "limit_minutes": SENSOR_STALE_AFTER.total_seconds() / 60,
        }
        if age is not None:
            params["silent_minutes"] = round(age.total_seconds() / 60)
        return Decision(ReasonCode.SAFETY_SENSOR_STALE, inputs.user_setpoint_c, now, params)
    if inputs.central_mode is CentralMode.STOP:
        return Decision(ReasonCode.CENTRAL_STOP, None, now)
    if inputs.central_mode is CentralMode.FROST_PROTECTION:
        return Decision(
            ReasonCode.FROST_PROTECTION,
            FROST_PROTECTION_SETPOINT_C,
            now,
            {"setpoint": FROST_PROTECTION_SETPOINT_C},
        )
    if window_active(inputs, now):
        params: dict[str, float | str] = {}
        if inputs.window_open_since is not None:
            params["open_minutes"] = round((now - inputs.window_open_since).total_seconds() / 60)
        if frost_guard_active(inputs):
            params["frost_guard"] = "on"
        return Decision(ReasonCode.WINDOW_OPEN, FROST_PROTECTION_SETPOINT_C, now, params)
    if inputs.startup_hold:
        return Decision(ReasonCode.STARTUP_HOLD, inputs.user_setpoint_c, now)
    return Decision(
        ReasonCode.SETPOINT, inputs.user_setpoint_c, now, {"setpoint": inputs.user_setpoint_c}
    )


def window_active(inputs: RoomInputs, now: datetime) -> bool:
    """RUL-014: close after the open delay; resume only after the closed delay."""
    opened = inputs.window_open_since
    if opened is not None and now - opened >= inputs.window_open_after:
        return True
    if not inputs.window_was_active:
        return False
    if opened is not None:
        # Re-opened during the resume delay (e.g. switching to tilted): stay closed.
        return True
    closed = inputs.window_closed_since
    return closed is not None and now - closed < inputs.window_resume_after


def frost_guard_active(inputs: RoomInputs) -> bool:
    """RUL-015: heat to the frost setpoint although the window is open."""
    room = inputs.room_temperature_c
    if room is None:
        return inputs.frost_guard_was_active
    if room < FROST_PROTECTION_SETPOINT_C:
        return True
    if room > FROST_PROTECTION_SETPOINT_C + FROST_GUARD_HYSTERESIS_K:
        return False
    return inputs.frost_guard_was_active


def is_closed_for_window(decision: Decision) -> bool:
    """The valve stays closed: window open and no frost guard."""
    return decision.code is ReasonCode.WINDOW_OPEN and "frost_guard" not in decision.params
