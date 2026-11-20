# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta

from custom_components.thermogeist.core.decisions import (
    ReasonCode,
    RoomInputs,
    Severity,
    decide_room,
)
from custom_components.thermogeist.core.house import CentralMode
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

START = datetime(2026, 11, 20, 6, 0, tzinfo=UTC)


def inputs(
    mode: CentralMode = CentralMode.AUTO, valid_since: datetime | None = START
) -> RoomInputs:
    return RoomInputs(user_setpoint_c=21.0, central_mode=mode, temperature_valid_since=valid_since)


def test_normal_operation_holds_setpoint() -> None:
    """Scenario: SCN-DEC-001"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(minutes=5))

    decision = decide_room(inputs(), clock)

    assert decision.code is ReasonCode.SETPOINT
    assert decision.target_setpoint_c == 21.0
    assert decision.severity is Severity.INFO
    assert decision.timestamp == clock.now()


def test_central_mode_overrides_setpoint() -> None:
    """Scenario: SCN-DEC-002"""
    clock = FakeTimeProvider(START)

    stop = decide_room(inputs(CentralMode.STOP), clock)
    assert stop.code is ReasonCode.CENTRAL_STOP
    assert stop.target_setpoint_c is None

    frost = decide_room(inputs(CentralMode.FROST_PROTECTION), clock)
    assert frost.code is ReasonCode.FROST_PROTECTION
    assert frost.target_setpoint_c == 7.0


def test_sensor_becomes_stale_after_60_minutes() -> None:
    """Scenario: SCN-DEC-003"""
    clock = FakeTimeProvider(START)

    clock.advance(timedelta(minutes=59, seconds=59))
    assert decide_room(inputs(), clock).code is ReasonCode.SETPOINT

    clock.advance(timedelta(seconds=1))
    stale = decide_room(inputs(), clock)
    assert stale.code is ReasonCode.SAFETY_SENSOR_STALE
    assert stale.params == {"silent_minutes": 60, "limit_minutes": 60.0}
    assert stale.target_setpoint_c == 21.0
    assert stale.severity is Severity.SAFETY


def test_safety_has_precedence_over_central_mode() -> None:
    """Scenario: SCN-DEC-004"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(hours=2))

    assert decide_room(inputs(CentralMode.STOP), clock).code is ReasonCode.SAFETY_SENSOR_STALE


def test_never_reported_is_stale() -> None:
    """Scenario: SCN-DEC-005"""
    decision = decide_room(inputs(valid_since=None), FakeTimeProvider(START))

    assert decision.code is ReasonCode.SAFETY_SENSOR_STALE
    assert "silent_minutes" not in decision.params


def test_window_counts_after_30_seconds() -> None:
    """Scenario: SCN-DEC-006"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(minutes=5))
    opened = clock.now()

    clock.advance(timedelta(seconds=29))
    assert decide_room(inputs_with(window=opened), clock).code is ReasonCode.SETPOINT

    clock.advance(timedelta(seconds=1))
    window = decide_room(inputs_with(window=opened), clock)
    assert window.code is ReasonCode.WINDOW_OPEN
    assert window.target_setpoint_c == 7.0

    stopped = decide_room(inputs_with(window=opened, mode=CentralMode.STOP), clock)
    assert stopped.code is ReasonCode.CENTRAL_STOP


def test_startup_hold_is_shown_until_writes_start() -> None:
    """Scenario: SCN-DEC-007"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(minutes=1))

    held = decide_room(inputs_with(startup_hold=True), clock)
    assert held.code is ReasonCode.STARTUP_HOLD
    assert held.target_setpoint_c == 21.0


def inputs_with(
    window: datetime | None = None,
    mode: CentralMode = CentralMode.AUTO,
    startup_hold: bool = False,
) -> RoomInputs:
    return RoomInputs(
        user_setpoint_c=21.0,
        central_mode=mode,
        temperature_valid_since=START,
        window_open_since=window,
        startup_hold=startup_hold,
    )
