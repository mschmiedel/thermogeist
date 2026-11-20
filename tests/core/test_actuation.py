# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta

from custom_components.thermogeist.core.actuation import should_write
from custom_components.thermogeist.core.controller import (
    ControllerInputs,
    ControllerSettings,
    RoomController,
)
from custom_components.thermogeist.core.time_provider import FakeTimeProvider

START = datetime(2026, 12, 1, tzinfo=UTC)
HEAT_PUMP = ControllerSettings(min_opening_pct=30.0, dead_band_k=0.5, max_change_pct_per_30min=10.0)


def test_slow_ramp_is_written_in_few_bigger_steps() -> None:
    """Scenario: SCN-CTL-012"""
    clock = FakeTimeProvider(START)
    controller = RoomController()
    moves = writes = 0
    last_output = written = written_at = None
    for minute in range(150):
        feed_forward = 30.0 if minute == 0 else 67.0
        output = controller.step(
            ControllerInputs(20.0, 20.0, feed_forward, 10.0, False, HEAT_PUMP), clock.now()
        ).output_pct
        if last_output is not None and output != last_output:
            moves += 1
        last_output = output
        if should_write(output, written, written_at, clock.now()):
            if written is not None:
                writes += 1
            written, written_at = output, clock.now()
        clock.advance(timedelta(minutes=1))

    assert last_output == 67.0
    assert written == 67.0
    assert moves >= 30  # 1 % every ~3 minutes, as seen in the field
    assert writes <= 12


def test_urgent_changes_are_written_at_once() -> None:
    """Scenario: SCN-CTL-013"""
    now = START + timedelta(minutes=1)
    assert should_write(0.0, 45.0, START, now, urgent=True)
    assert not should_write(47.0, 45.0, START, now)
    assert not should_write(45.0, 45.0, START, START + timedelta(hours=1), urgent=True)
    assert should_write(48.0, 45.0, START, START + timedelta(minutes=10))
    assert not should_write(47.0, 45.0, START, START + timedelta(minutes=29))
    assert should_write(47.0, 45.0, START, START + timedelta(minutes=30))
