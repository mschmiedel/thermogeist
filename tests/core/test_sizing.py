# SPDX-License-Identifier: MIT
"""Radiator sizing and the learned heating curve (spec MDL-015, DIA-001 to DIA-015)."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.thermogeist.core.sizing import (
    Basis,
    Cause,
    Confidence,
    CurveHour,
    HourCollector,
    Sizing,
    SizingInputs,
    assess,
    classify,
    fit_heating_curve,
    fully_open_in_cold,
)

START = datetime(2026, 11, 1, tzinfo=UTC)


def curve_hours(count: int, low_c: float, high_c: float, slope: float = -0.6) -> list[CurveHour]:
    step = (high_c - low_c) / (count - 1)
    return [
        CurveHour(START + timedelta(hours=i), low_c + i * step, 35.0 + slope * (low_c + i * step))
        for i in range(count)
    ]


def test_classification_thresholds() -> None:
    """Scenario: SCN-SIZING-001"""
    assert classify(29.9) is Sizing.HEAVILY_OVERSIZED
    assert classify(30.0) is Sizing.RIGHT_SIZE
    assert classify(90.0) is Sizing.RIGHT_SIZE
    assert classify(95.0) is Sizing.TIGHT
    assert classify(100.0) is Sizing.TIGHT
    assert classify(100.1) is Sizing.UNDERSIZED


def test_heating_curve_is_learned_carefully() -> None:
    """Scenario: SCN-SIZING-002"""
    assert fit_heating_curve(curve_hours(47, 2.0, 12.0)) is None
    assert fit_heating_curve(curve_hours(48, 2.0, 6.0)) is None
    assert fit_heating_curve(curve_hours(48, 2.0, 12.0, slope=0.3)) is None

    curve = fit_heating_curve(curve_hours(48, 2.0, 12.0))
    assert curve is not None
    assert curve.flow_at(-10.5) == pytest.approx(41.3)
    assert curve.confidence_at(-10.5) is Confidence.MEDIUM
    assert curve.confidence_at(-20.0) is Confidence.LOW
    assert curve.confidence_at(0.0) is Confidence.HIGH


LIVING_ROOM = SizingInputs(
    heat_loss_w_per_k=39.43,
    setpoint_c=21.5,
    design_outdoor_c=-10.5,
    rated_output_w=2165.0,
    has_flow_sensor=True,
    curve=fit_heating_curve(curve_hours(48, 2.0, 12.0)),
    spread_k=2.9,
    full_open_hours=0,
    heat_pump=True,
)


def test_assessment() -> None:
    """Scenario: SCN-SIZING-003"""
    result = assess(LIVING_ROOM)
    assert result.sizing is Sizing.UNDERSIZED
    assert result.design_demand_w == pytest.approx(1261.8, abs=0.5)
    assert result.design_output_w == pytest.approx(591, abs=2)
    assert result.load_pct == pytest.approx(213, abs=1)
    assert (result.cause, result.basis, result.confidence) == (
        Cause.RADIATOR_SMALL,
        Basis.STATIC,
        Confidence.MEDIUM,
    )

    pump = assess(replace(LIVING_ROOM, rated_output_w=20000.0))
    assert pump.sizing is Sizing.HEAVILY_OVERSIZED
    assert pump.reserve is True
    assert pump.cause is Cause.RADIATOR_LARGE
    boiler = assess(replace(LIVING_ROOM, rated_output_w=20000.0, heat_pump=False))
    assert boiler.reserve is False

    unknown = assess(replace(LIVING_ROOM, heat_loss_w_per_k=None, has_flow_sensor=False))
    assert unknown.sizing is Sizing.NOT_ASSESSABLE
    assert unknown.missing == ("heat_load", "flow_temperature")

    fine = replace(LIVING_ROOM, rated_output_w=6000.0, full_open_hours=6)
    operation = assess(fine)
    assert operation.sizing is Sizing.UNDERSIZED
    assert (operation.basis, operation.cause) == (Basis.OPERATION, Cause.INPUT_OR_HYDRAULICS)


def test_hour_collector() -> None:
    """Scenario: SCN-SIZING-004"""
    collector = HourCollector()
    ten = START.replace(hour=10)
    for minute in range(60):
        flow = 60.0 if minute == 30 else 38.0
        result = collector.add(
            ten + timedelta(minutes=minute),
            3.0,
            flow,
            20.0,
            {"living": minute < 55, "bath": minute < 50},
        )
        assert result is None
    finished = collector.add(ten + timedelta(hours=1), 3.0, 38.0, 20.0, {})
    assert finished is not None
    assert finished.hour == ten
    assert finished.curve_hour == CurveHour(ten, 3.0, 38.0)
    assert finished.full_open_rooms == {"living"}

    for minute in range(1, 60):
        collector.add(ten + timedelta(hours=1, minutes=minute), 3.0, 23.0, 20.0, {})
    off = collector.add(ten + timedelta(hours=2), 3.0, 23.0, 20.0, {})
    assert off is not None and off.curve_hour is None

    assert fully_open_in_cold(95.0, 20.4, 21.0, 4.9, True)
    assert not fully_open_in_cold(94.0, 20.4, 21.0, 4.9, True)
    assert not fully_open_in_cold(95.0, 20.5, 21.0, 4.9, True)
    assert not fully_open_in_cold(95.0, 20.4, 21.0, 5.0, True)
    assert not fully_open_in_cold(95.0, 20.4, 21.0, 4.9, False)
