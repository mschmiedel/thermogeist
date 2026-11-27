# SPDX-License-Identifier: MIT
"""Heaters with stages (spec ACT-060 to ACT-067)."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.thermogeist.core.heater import (
    EnergySource,
    Heater,
    StageCycler,
    StagePlan,
    StageSource,
    available_w,
    current_stage,
    heater_fault,
    heater_feed_forward_pct,
    parse_outputs,
    parse_stage,
    stage_plan,
    validate_heater,
)

START = datetime(2026, 11, 26, 8, 0, tzinfo=UTC)


def convector(**changes: object) -> Heater:
    values: dict[str, object] = {
        "room_id": "kitchen",
        "name": "Plinth heater",
        "switch_entity": "switch.plinth",
        "energy_source": EnergySource.HEATING_CIRCUIT,
        "stage_outputs_w": (1300.0, 1700.0),
        "off_output_w": 40.0,
        "exponent": 1.0,
        "stage_setter": "number.plinth_stage",
    }
    values.update(changes)
    return Heater(**values)  # type: ignore[arg-type]


def test_heat_is_placed_between_neighbouring_stages() -> None:
    """Scenario: SCN-HEATER-001"""
    heater = convector()

    assert stage_plan(0, heater, running_stage=None) == StagePlan(0, 1, 0.0)
    half = stage_plan(50, heater, running_stage=None)
    assert (half.lower, half.upper) == (0, 1)
    assert half.upper_share == pytest.approx((850 - 40) / (1300 - 40))
    high = stage_plan(85, heater, running_stage=None)
    assert (high.lower, high.upper) == (1, 2)
    assert high.upper_share == pytest.approx((1445 - 1300) / 400)
    assert stage_plan(100, heater, running_stage=None) == StagePlan(1, 2, 1.0)


def test_without_setter_heater_runs_between_off_and_its_stage() -> None:
    """Scenario: SCN-HEATER-002"""
    heater = convector(off_output_w=0.0, stage_setter=None, stage_sensor="sensor.plinth_stage")

    half = stage_plan(50, heater, running_stage=1)
    assert (half.lower, half.upper) == (0, 1)
    assert half.upper_share == pytest.approx(850 / 1300)
    assert stage_plan(100, heater, running_stage=1) == StagePlan(0, 1, 1.0)


def _minutes_on(cycler: StageCycler, plan: StagePlan, start: datetime, minutes: int) -> list[int]:
    return [cycler.step(plan, start + timedelta(minutes=m)) for m in range(minutes)]


def test_minimum_run_time_is_carried_over() -> None:
    """Scenario: SCN-HEATER-003"""
    cycler = StageCycler()
    plan = StagePlan(0, 1, 0.15)

    stages = _minutes_on(cycler, plan, START, 80)

    assert sum(stages[0:20]) == 0
    assert sum(stages[20:40]) == 6
    assert sum(stages) == 12


def test_new_plan_waits_for_next_cycle_and_interrupt_is_immediate() -> None:
    """Scenario: SCN-HEATER-004"""
    cycler = StageCycler()
    full = StagePlan(0, 1, 1.0)

    assert cycler.step(StagePlan(0, 1, 0.5), START) == 1
    assert cycler.step(full, START + timedelta(minutes=5)) == 1
    assert cycler.step(full, START + timedelta(minutes=10)) == 0
    cycler.interrupt()
    restart = START + timedelta(minutes=13)
    assert cycler.cycle_start is None
    assert _minutes_on(cycler, full, restart, 20) == [1] * 20
    assert cycler.cycle_start == restart


def test_heating_circuit_output_and_linear_feed_forward() -> None:
    """Scenario: SCN-HEATER-005"""
    fan = convector()
    panel = Heater("kitchen", "Panel", "switch.panel", EnergySource.DIRECT, (600.0,))

    fan_top = available_w(fan, 2, 37.5, 20.0, 5.0)
    assert fan_top == pytest.approx(1700 * 15 / 49.8)
    assert available_w(panel, 1, None, None) == 600.0
    assert heater_feed_forward_pct(400, [fan, panel], 37.5, 20.0, 5.0) == pytest.approx(
        100 * 400 / (fan_top + 600)
    )
    assert heater_feed_forward_pct(400, [fan, panel], None, 20.0) is None
    assert heater_feed_forward_pct(400, [panel], None, 20.0) == pytest.approx(100 * 400 / 600)


def test_fault_when_switched_on_but_not_running() -> None:
    """Scenario: SCN-HEATER-006"""

    def at(minutes: float) -> datetime:
        return START + timedelta(minutes=minutes)

    zero = at(-30)
    fault = heater_fault(on_since=START, zero_since=zero, stage=0, now=at(2), was_fault=False)
    assert fault is False
    fault = heater_fault(on_since=START, zero_since=zero, stage=0, now=at(3), was_fault=fault)
    assert fault is True
    fault = heater_fault(on_since=None, zero_since=zero, stage=0, now=at(10), was_fault=fault)
    assert fault is True
    fault = heater_fault(on_since=None, zero_since=None, stage=1, now=at(20), was_fault=fault)
    assert fault is False

    by_hand = at(60)
    assert (
        heater_fault(on_since=START, zero_since=by_hand, stage=0, now=at(60.15), was_fault=False)
        is False
    )


def test_heater_entries_are_checked() -> None:
    """Scenario: SCN-HEATER-007"""

    def check(stages: int, outputs: list[float], **kw: object) -> dict[str, str]:
        values: dict[str, object] = {
            "off_output_w": 40.0,
            "exponent": 1.0,
            "has_stage_sensor": True,
            "has_stage_setter": False,
        }
        values.update(kw)
        return validate_heater(stages, outputs, **values)  # type: ignore[arg-type]

    assert check(2, [1300, 1700]) == {}
    assert check(2, [1300]) == {"stage_outputs": "heater_outputs_count"}
    assert check(2, [1700, 1300]) == {"stage_outputs": "heater_outputs_rising"}
    assert check(2, [1300, 1700], has_stage_sensor=False) == {
        "stage_sensor": "heater_needs_stage_entity"
    }
    assert check(2, [1300, 1700], exponent=3.0) == {"exponent": "heater_exponent_range"}
    assert check(6, [1, 2, 3, 4, 5, 6]) == {"stages": "heater_stages_range"}
    assert parse_outputs("1300; 1700") == [1300.0, 1700.0]
    assert parse_outputs("1300, viel") is None


def test_current_stage_sources() -> None:
    """Scenario: SCN-HEATER-008"""
    sensed = convector(stage_sensor="sensor.plinth_stage", stage_setter=None)
    assert [parse_stage(v, 2) for v in ("2", "1.0", "1.5", "7", "unavailable")] == [
        2,
        1,
        None,
        None,
        None,
    ]
    assert current_stage(sensed, switch_on=True, sensor_stage=None, setter_stage=None) == (
        None,
        StageSource.STAGE_SENSOR,
    )

    set_only = convector()
    assert current_stage(set_only, switch_on=True, sensor_stage=None, setter_stage=2) == (
        2,
        StageSource.STAGE_SETTER,
    )
    assert current_stage(set_only, switch_on=False, sensor_stage=None, setter_stage=2) == (
        0,
        StageSource.SWITCH,
    )

    plain = Heater("kitchen", "Panel", "switch.panel", EnergySource.DIRECT, (600.0,))
    assert current_stage(plain, switch_on=True, sensor_stage=None, setter_stage=None) == (
        1,
        StageSource.SWITCH,
    )
    assert current_stage(plain, switch_on=False, sensor_stage=None, setter_stage=None)[0] == 0
