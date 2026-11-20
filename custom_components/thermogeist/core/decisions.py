# SPDX-License-Identifier: MIT
"""The central decision point and reason catalogue (spec ARC-003, RSN-001, RSN-002, RUL-013).

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


CATALOGUE: dict[ReasonCode, Severity] = {
    ReasonCode.SETPOINT: Severity.INFO,
    ReasonCode.CENTRAL_STOP: Severity.NOTICE,
    ReasonCode.FROST_PROTECTION: Severity.NOTICE,
    ReasonCode.SAFETY_SENSOR_STALE: Severity.SAFETY,
}

# RUL-013: a room temperature older than this is not trusted. Zigbee sensors usually report at
# least every few minutes; an hour of silence means a dead battery or lost connection.
SENSOR_STALE_AFTER = timedelta(minutes=60)


@dataclass(frozen=True, slots=True)
class RoomInputs:
    """What the decision for one room depends on."""

    user_setpoint_c: float
    central_mode: CentralMode
    temperature_valid_since: datetime | None
    """Last time the room temperature sensor reported a valid value."""


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
    """Apply the fixed precedence (RUL-030): safety, central mode, user setpoint."""
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
    return Decision(
        ReasonCode.SETPOINT, inputs.user_setpoint_c, now, {"setpoint": inputs.user_setpoint_c}
    )
