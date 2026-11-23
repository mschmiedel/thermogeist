# SPDX-License-Identifier: MIT
"""Lost calibration from the device's own report (spec DIA-024)."""

from datetime import UTC, datetime, timedelta

from custom_components.thermogeist.core.calibration import (
    CALIBRATION_LOST_AFTER,
    CalibrationWatch,
    is_uncalibrated,
)

NOW = datetime(2026, 11, 22, 21, 24, tzinfo=UTC)
BOSCH = ("none", "ready_to_calibrate", "error")


def test_profile_values_mean_not_calibrated() -> None:
    """Scenario: SCN-CALIB-001"""
    assert is_uncalibrated("0", ("0",)) is True
    assert is_uncalibrated("0.0", ("0",)) is True
    assert is_uncalibrated("337", ("0",)) is False
    assert is_uncalibrated("ready_to_calibrate", BOSCH) is True
    assert is_uncalibrated("success", BOSCH) is False
    assert is_uncalibrated(None, ("0",)) is None


def test_only_a_lasting_state_counts() -> None:
    """Scenario: SCN-CALIB-002"""
    watch = CalibrationWatch()

    assert not watch.update(True, NOW)  # e.g. during a calibration
    assert not watch.update(False, NOW + timedelta(minutes=1))
    assert not watch.update(True, NOW + timedelta(minutes=2))
    assert not watch.update(None, NOW + timedelta(minutes=5))
    assert not watch.lost

    assert watch.update(True, NOW + timedelta(minutes=2) + CALIBRATION_LOST_AFTER)
    assert watch.lost
    assert not watch.update(True, NOW + timedelta(hours=1))

    assert watch.update(False, NOW + timedelta(hours=9))
    assert not watch.lost
