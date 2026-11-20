# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.thermogeist.core.smoothing import MovingAverage, plausible_flow

START = datetime(2026, 12, 1, tzinfo=UTC)


def test_flow_is_averaged_over_30_minutes_and_checked() -> None:
    """Scenario: SCN-SMOOTH-001"""
    average = MovingAverage()
    for minute, value in enumerate([32.5, 32.25] * 10 + [28.0]):
        average.add(START + timedelta(minutes=minute), value)

    assert average.value(START + timedelta(minutes=20)) == pytest.approx(
        (32.5 * 10 + 32.25 * 10 + 28.0) / 21
    )
    assert average.value(START + timedelta(minutes=60)) is None
    assert plausible_flow(29.0)
    assert not plausible_flow(85.0)
    assert not plausible_flow(-127.0)
    assert not plausible_flow(None)
