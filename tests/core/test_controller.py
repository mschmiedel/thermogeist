# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.thermogeist.core.controller import (
    ControllerInputs,
    ControllerSettings,
    Limit,
    RoomController,
    feed_forward_pct,
)
from custom_components.thermogeist.core.radiator import available_output_w, time_constant_h
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

HEAT_PUMP = ControllerSettings(min_opening_pct=40.0, dead_band_k=0.5, max_change_pct_per_30min=10.0)
START = datetime(2026, 12, 1, tzinfo=UTC)


def inputs(**overrides: object) -> ControllerInputs:
    values: dict[str, object] = {
        "target_c": 20.0,
        "room_c": 20.0,
        "feed_forward_pct": 60.0,
        "time_constant_h": 10.0,
        "safety": False,
        "settings": HEAT_PUMP,
    }
    values.update(overrides)
    return ControllerInputs(**values)  # type: ignore[arg-type]


def test_feed_forward_inverts_typical_valve_characteristic() -> None:
    """Scenario: SCN-CTL-007"""
    available = available_output_w(2000.0, 40.0, 20.0)
    assert available == pytest.approx(2000.0 * (17.5 / 49.8) ** 1.3)
    fraction = 400.0 / available
    assert feed_forward_pct(400.0, 2000.0, 40.0, 20.0) == pytest.approx(10 + 90 * fraction**2)
    assert feed_forward_pct(400.0, 2000.0, 22.0, 20.0) == 100.0
    assert feed_forward_pct(None, 2000.0, 40.0, 20.0) is None
    assert feed_forward_pct(400.0, None, 40.0, 20.0) is None
    assert time_constant_h(20.0, 20.0) == pytest.approx(46.0)


def test_stop_and_safety_override_regulation() -> None:
    """Scenario: SCN-CTL-006"""
    clock = FakeTimeProvider(START)
    controller = RoomController()

    stopped = controller.step(inputs(target_c=None), clock.now())
    assert stopped.output_pct == 0.0
    assert stopped.limits == (Limit.STOPPED,)

    clock.advance(timedelta(minutes=1))
    safe = controller.step(inputs(safety=True), clock.now())
    assert safe.output_pct == 40.0
    assert safe.limits == (Limit.SAFETY,)

    boiler = ControllerSettings(min_opening_pct=0.0, dead_band_k=0.2, max_change_pct_per_30min=30.0)
    safe_boiler = RoomController().step(inputs(safety=True, settings=boiler), clock.now())
    assert safe_boiler.output_pct == 20.0


def test_dead_band_calms_proportional_part_only() -> None:
    """Scenario: SCN-CTL-008"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    first = controller.step(inputs(room_c=20.4), clock.now())
    assert first.proportional_pct == 0.0
    assert first.output_pct == 60.0

    clock.advance(timedelta(hours=1))
    second = controller.step(inputs(room_c=20.4), clock.now())
    assert second.proportional_pct == 0.0
    # The result shows the integral used for this step; the updated value applies next step.
    assert controller.state.integral_pct == pytest.approx(-15.0 * 0.4 * 1 / 10.0)


def test_output_does_not_twitch_on_rounding() -> None:
    """Scenario: SCN-CTL-009"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    outputs = []
    for ff in (60.4, 60.6, 60.4, 60.6):
        outputs.append(controller.step(inputs(feed_forward_pct=ff), clock.now()).output_pct)
        clock.advance(timedelta(minutes=1))
    clock.advance(timedelta(minutes=10))  # long enough for the rate limit
    outputs.append(controller.step(inputs(feed_forward_pct=61.2), clock.now()).output_pct)
    assert outputs == [60.0, 60.0, 60.0, 60.0, 61.0]


def test_window_closes_at_once_and_resumes_where_it_was() -> None:
    """Scenario: SCN-CTL-010"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    before = controller.step(inputs(feed_forward_pct=60.0), clock.now())
    assert before.output_pct == 60.0

    clock.advance(timedelta(minutes=1))
    window = controller.step(inputs(window_open=True), clock.now())
    assert window.output_pct == 0.0
    assert window.limits == (Limit.WINDOW,)

    clock.advance(timedelta(minutes=20))
    after = controller.step(inputs(feed_forward_pct=60.0), clock.now())
    assert after.output_pct == 60.0


def test_start_value_is_removed_when_feed_forward_arrives() -> None:
    """Scenario: SCN-CTL-011"""
    clock = FakeTimeProvider(START)
    controller = RoomController()

    controller.step(inputs(feed_forward_pct=None), clock.now())
    assert controller.state.integral_pct == 30.0

    clock.advance(timedelta(minutes=1))
    controller.step(inputs(feed_forward_pct=36.9), clock.now())
    assert controller.state.integral_pct == pytest.approx(0.0)

    clock.advance(timedelta(minutes=1))
    controller.step(inputs(feed_forward_pct=None), clock.now())
    assert controller.state.integral_pct == pytest.approx(30.0)


def test_room_above_target_never_gets_more_heat() -> None:
    """Scenario: SCN-CTL-014"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    first = controller.step(inputs(room_c=20.3, feed_forward_pct=30.0), clock.now())

    clock.advance(timedelta(minutes=15))
    result = controller.step(inputs(room_c=20.3, feed_forward_pct=54.0), clock.now())

    assert result.output_pct == first.output_pct  # 40 % minimum opening, no increase
    assert Limit.HOLD_WHEN_WARM in result.limits


def test_seeded_controller_is_rate_limited_from_the_first_step() -> None:
    """Scenario: SCN-CTL-015"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    controller.seed(30.0)

    result = controller.step(inputs(feed_forward_pct=54.0), clock.now())

    assert result.output_pct == 30.0
    assert Limit.RATE_LIMIT in result.limits


def test_state_survives_a_restart_but_not_a_long_outage() -> None:
    """Scenario: SCN-CTL-016"""
    before = RoomController()
    before.state.integral_pct = -7.5
    before.state.min_opening_relaxed = True
    snapshot = before.snapshot()
    saved = datetime(2026, 1, 15, 6, 0, tzinfo=UTC)

    after = RoomController()
    assert after.restore(snapshot, saved, saved + timedelta(minutes=5))
    assert after.state.integral_pct == -7.5
    assert after.state.min_opening_relaxed is True
    assert after.state.last_output_pct is None  # seeded from the valve instead (CTL-044)

    stale = RoomController()
    assert not stale.restore(snapshot, saved, saved + timedelta(hours=25))
    assert stale.state.integral_pct is None


def test_lasting_overshoot_lowers_the_correction() -> None:
    """Scenario: SCN-CTL-019"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    for _ in range(121):
        controller.step(inputs(target_c=21.5, room_c=22.8, feed_forward_pct=100.0), clock.now())
        clock.advance(timedelta(minutes=1))
    lowered = controller.state.integral_pct
    assert lowered is not None and lowered < -1.0

    for _ in range(120):
        controller.step(inputs(target_c=21.5, room_c=19.5, feed_forward_pct=100.0), clock.now())
        clock.advance(timedelta(minutes=1))
    assert controller.state.integral_pct == pytest.approx(lowered)


def test_window_open_from_the_start_returns_at_once() -> None:
    """Scenario: SCN-CTL-020"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    # After a restart the controller starts from the reported valve: closed by the window.
    controller.seed(0.0)
    for _ in range(30):
        window = controller.step(inputs(window_open=True), clock.now())
        clock.advance(timedelta(minutes=1))
    assert window.output_pct == 0.0
    assert window.limits == (Limit.WINDOW,)

    closed = controller.step(inputs(room_c=19.4, feed_forward_pct=60.0), clock.now())
    assert closed.output_pct == 69.0
    assert Limit.RATE_LIMIT not in closed.limits

    clock.advance(timedelta(minutes=1))
    later = controller.step(inputs(room_c=19.4, feed_forward_pct=90.0), clock.now())
    assert later.output_pct == pytest.approx(69.0, abs=1)
    assert Limit.RATE_LIMIT in later.limits


def test_safe_position_is_no_starting_point() -> None:
    """Scenario: SCN-CTL-021"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    warm = {"target_c": 19.5, "room_c": 21.0, "feed_forward_pct": 10.0}
    for _ in range(120):
        lowest = controller.step(inputs(**warm), clock.now())
        clock.advance(timedelta(minutes=1))
    assert lowest.output_pct < 40.0

    restart = controller.step(inputs(**{**warm, "room_c": None}), clock.now())
    assert restart.output_pct == 40.0
    assert restart.limits == (Limit.SAFETY,)

    clock.advance(timedelta(minutes=1))
    back = controller.step(inputs(**warm), clock.now())
    assert back.output_pct == pytest.approx(lowest.output_pct, abs=1)
    assert Limit.RATE_LIMIT not in back.limits
