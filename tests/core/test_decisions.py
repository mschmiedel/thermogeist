# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta
from typing import Any

from custom_components.thermogeist.core.decisions import (
    Decision,
    ReasonCode,
    RoomInputs,
    Severity,
    decide_room,
    is_closed_for_window,
)
from custom_components.thermogeist.core.house import CentralMode
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

START = datetime(2026, 11, 20, 6, 0, tzinfo=UTC)


def inputs(
    mode: CentralMode = CentralMode.AUTO,
    valid_since: datetime | None = START,
    unavailable_since: datetime | None = None,
) -> RoomInputs:
    return RoomInputs(
        user_setpoint_c=21.0,
        central_mode=mode,
        temperature_valid_since=valid_since,
        temperature_unavailable_since=unavailable_since,
    )


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


def test_silent_sensor_is_flagged_after_6_hours() -> None:
    """Scenario: SCN-DEC-003"""
    clock = FakeTimeProvider(START)

    clock.advance(timedelta(hours=5, minutes=59, seconds=59))
    assert decide_room(inputs(), clock).code is ReasonCode.SETPOINT

    clock.advance(timedelta(seconds=1))
    stale = decide_room(inputs(), clock)
    assert stale.code is ReasonCode.SAFETY_SENSOR_STALE
    assert stale.params == {"cause": "silent", "silent_minutes": 360, "limit_minutes": 360.0}
    assert stale.target_setpoint_c == 21.0
    assert stale.severity is Severity.SAFETY


def test_safety_has_precedence_over_central_mode() -> None:
    """Scenario: SCN-DEC-004"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(hours=7))

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
    **extra: Any,
) -> RoomInputs:
    return RoomInputs(
        user_setpoint_c=21.0,
        central_mode=mode,
        temperature_valid_since=START,
        window_open_since=window,
        startup_hold=startup_hold,
        **extra,
    )


def test_heating_resumes_only_after_the_resume_delay() -> None:
    """Scenario: SCN-DEC-008"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(minutes=5))
    closed = clock.now()

    clock.advance(timedelta(seconds=9))
    still = decide_room(inputs_with(window_closed_since=closed, window_was_active=True), clock)
    assert still.code is ReasonCode.WINDOW_OPEN
    # Switching to tilted: open again for a moment during the resume delay.
    reopened = decide_room(inputs_with(window=clock.now(), window_was_active=True), clock)
    assert reopened.code is ReasonCode.WINDOW_OPEN

    clock.advance(timedelta(seconds=1))
    resumed = decide_room(inputs_with(window_closed_since=closed, window_was_active=True), clock)
    assert resumed.code is ReasonCode.SETPOINT

    # A custom close delay of 0 s closes at once.
    now_open = decide_room(inputs_with(window=clock.now(), window_open_after=timedelta()), clock)
    assert now_open.code is ReasonCode.WINDOW_OPEN


def test_frost_guard_heats_a_cold_room_with_open_window() -> None:
    """Scenario: SCN-DEC-009"""
    clock = FakeTimeProvider(START)
    clock.advance(timedelta(minutes=5))
    opened = START

    def decide(room_c: float, was_active: bool) -> Decision:
        return decide_room(
            inputs_with(
                window=opened,
                room_temperature_c=room_c,
                frost_guard_was_active=was_active,
            ),
            clock,
        )

    cold = decide(6.9, False)
    assert cold.params["frost_guard"] == "on"
    assert cold.target_setpoint_c == 7.0
    assert not is_closed_for_window(cold)
    assert "frost_guard" in decide(7.8, True).params  # hysteresis
    assert "frost_guard" not in decide(8.1, True).params
    assert is_closed_for_window(decide(7.5, False))


def test_unavailable_sensor_is_flagged_after_15_minutes() -> None:
    """Scenario: SCN-DEC-010"""
    clock = FakeTimeProvider(START + timedelta(minutes=44, seconds=59))
    gone = START + timedelta(minutes=30)

    assert decide_room(inputs(unavailable_since=gone), clock).code is ReasonCode.SETPOINT

    clock.advance(timedelta(seconds=1))
    stale = decide_room(inputs(unavailable_since=gone), clock)
    assert stale.code is ReasonCode.SAFETY_SENSOR_STALE
    assert stale.params["cause"] == "unavailable"
    assert stale.params["unavailable_minutes"] == 15
