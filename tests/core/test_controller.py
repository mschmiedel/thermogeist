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
