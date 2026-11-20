# SPDX-License-Identifier: MIT
"""Setpoint strategy: what to send to a thermostat that regulates itself (spec ACT-050 to ACT-054).

Some thermostats cannot or should not be driven by valve position. Thermogeist then tells them
which temperature to aim for and lets their own controller move the valve.
"""

from __future__ import annotations

from datetime import datetime, timedelta

# ACT-052: the range thermostats accept almost universally.
DEVICE_SETPOINT_MIN_C = 5.0
DEVICE_SETPOINT_MAX_C = 30.0
# Most thermostats accept 0.5 K steps; finer values are rounded by the device anyway.
SETPOINT_STEP_K = 0.5
# ACT-052: closed state for window and stop. 5 °C still protects against frost.
CLOSED_SETPOINT_C = DEVICE_SETPOINT_MIN_C
# ACT-053: bundling of setpoint writes, like valve writes.
MIN_SETPOINT_CHANGE_K = 0.5
MIN_SETPOINT_INTERVAL = timedelta(minutes=10)


def round_setpoint(value_c: float) -> float:
    """Round to 0.5 K and keep within 5-30 °C."""
    rounded = round(value_c / SETPOINT_STEP_K) * SETPOINT_STEP_K
    return min(DEVICE_SETPOINT_MAX_C, max(DEVICE_SETPOINT_MIN_C, rounded))


def device_setpoint_c(
    target_c: float | None,
    room_c: float | None,
    device_c: float | None,
    *,
    external_input: bool,
) -> float:
    """The setpoint for the device.

    With an external temperature input the device regulates on the room temperature, so the
    room target is sent unchanged (ACT-051). Without it the device measures next to the hot
    radiator; the measured offset is added so it aims at the right room temperature (ACT-052).
    ``target_c`` None means: do not heat.
    """
    if target_c is None:
        return CLOSED_SETPOINT_C
    if external_input or room_c is None or device_c is None:
        return round_setpoint(target_c)
    return round_setpoint(target_c + (device_c - room_c))


def should_write_setpoint(
    desired_c: float,
    last_written_c: float | None,
    last_written_at: datetime | None,
    now: datetime,
    *,
    urgent: bool = False,
) -> bool:
    """ACT-053: only meaningful changes, at most every 10 minutes; urgent ones at once."""
    if last_written_c is None or last_written_at is None:
        return True
    difference = abs(desired_c - last_written_c)
    if difference == 0:
        return False
    if urgent:
        return True
    return difference >= MIN_SETPOINT_CHANGE_K and now - last_written_at >= MIN_SETPOINT_INTERVAL
