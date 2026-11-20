# SPDX-License-Identifier: MIT
"""Setpoint strategy (spec ACT-051 to ACT-053) and measured spread (MDL-019)."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.thermogeist.core.controller import feed_forward_pct
from custom_components.thermogeist.core.radiator import available_output_w, usable_spread_k
from custom_components.thermogeist.core.setpoint import (
    CLOSED_SETPOINT_C,
    device_setpoint_c,
    should_write_setpoint,
)

T0 = datetime(2026, 1, 15, 6, 0, tzinfo=UTC)


def test_external_input_sends_the_room_target() -> None:
    """Scenario: SCN-SETPOINT-001"""
    assert device_setpoint_c(21.0, 19.0, 24.0, external_input=True) == 21.0


def test_offset_compensates_the_device_sensor() -> None:
    """Scenario: SCN-SETPOINT-002"""
    # The device measures 2.4 K more than the room next to the warm radiator.
    assert device_setpoint_c(20.0, 19.6, 22.0, external_input=False) == 22.5
    # Without a device reading the room target is sent unchanged.
    assert device_setpoint_c(20.0, 19.6, None, external_input=False) == 20.0


def test_setpoint_is_rounded_and_limited() -> None:
    """Scenario: SCN-SETPOINT-003"""
    assert device_setpoint_c(28.0, 18.0, 25.0, external_input=False) == 30.0
    assert device_setpoint_c(7.0, 22.0, 18.0, external_input=False) == 5.0
    assert device_setpoint_c(20.2, None, None, external_input=False) == 20.0
    assert device_setpoint_c(None, 19.0, 22.0, external_input=False) == CLOSED_SETPOINT_C


def test_setpoint_writes_are_bundled() -> None:
    """Scenario: SCN-SETPOINT-004"""
    assert should_write_setpoint(20.0, None, None, T0)
    assert not should_write_setpoint(20.0, 20.0, T0, T0 + timedelta(hours=1))
    assert not should_write_setpoint(20.5, 20.0, T0, T0 + timedelta(minutes=9))
    assert should_write_setpoint(20.5, 20.0, T0, T0 + timedelta(minutes=10))
    assert should_write_setpoint(5.0, 20.0, T0, T0 + timedelta(seconds=30), urgent=True)


def test_measured_spread_replaces_the_assumption() -> None:
    """Scenario: SCN-HEAT-004"""
    assert usable_spread_k(None, 30.0) is None
    assert usable_spread_k(40.0, 33.0) == 7.0
    assert usable_spread_k(40.0, 39.8) == 1.0  # limited
    assert usable_spread_k(40.0, 20.0) == 10.0  # limited
    assumed = available_output_w(1000.0, 40.0, 20.0)
    assert available_output_w(1000.0, 40.0, 20.0, 5.0) == pytest.approx(assumed)
    assert available_output_w(1000.0, 40.0, 20.0, 8.0) < assumed
    # Less output per opening → the feed-forward opens further.
    assert feed_forward_pct(100.0, 1000.0, 40.0, 20.0, 8.0) > feed_forward_pct(
        100.0, 1000.0, 40.0, 20.0, 5.0
    )
