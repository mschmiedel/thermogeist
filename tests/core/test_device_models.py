# SPDX-License-Identifier: MIT
"""Device models fitted to field data, and the setpoint strategy against them (spec TST-012,
TST-015, ACT-050 to ACT-053)."""

from datetime import timedelta
from statistics import fmean

from tests.sim.devices import BthRaModel, ShcModel, load_recording, replay_error_pct
from tests.sim.room import SimRoom
from tests.sim.setpoint_run import SetpointScenario, run_setpoint

MINUTES_PER_DAY = 24 * 60


def test_bth_ra_model_reproduces_the_recorded_day() -> None:
    """Scenario: SCN-DEV-001"""
    recording = load_recording("bosch_bth_ra_day.csv")

    assert replay_error_pct(BthRaModel(), recording) <= 4.0


def test_shc_model_reproduces_the_recorded_days() -> None:
    """Scenario: SCN-DEV-002"""
    for name in ("bosch_shc_day.csv", "bosch_shc_day2.csv"):
        assert replay_error_pct(ShcModel(), load_recording(name)) <= 4.0, name


def test_shc_window_function_closes_and_reopens() -> None:
    """Scenario: SCN-DEV-003"""
    model = ShcModel()
    for _ in range(60):
        model.step(1, 21.0, 21.0)

    closed = model.step(1, 21.0, 19.8)  # window: 1.2 K drop within a minute
    after = [model.step(1, 21.0, 19.8) for _ in range(40)]

    assert closed == 0.0
    assert after[-1] >= 50.0  # 1.2 K below the setpoint: the band opens wide again


def bathroom() -> SimRoom:
    """Small room, radiator able to cover it with margin (like the recorded guest bathroom)."""
    return SimRoom(floor_area_m2=5, heat_loss_w_per_k=8, rated_output_w=800, temperature_c=19.0)


def dining_room() -> SimRoom:
    return SimRoom(floor_area_m2=20, heat_loss_w_per_k=25, rated_output_w=3000, temperature_c=19.0)


def test_setpoint_strategy_holds_the_room_with_a_bth_ra() -> None:
    """Scenario: SCN-DEV-004"""
    trace = run_setpoint(
        SetpointScenario(bathroom(), BthRaModel(), external_input=True), timedelta(days=2)
    )

    day_2 = trace.temperatures[MINUTES_PER_DAY:]
    assert max(day_2) - 20.5 <= 0.5
    assert fmean(abs(t - 20.5) for t in day_2) <= 0.3
    assert trace.writes <= 2  # the room target is sent once; no chasing


def test_setpoint_strategy_holds_the_room_with_a_shc() -> None:
    """Scenario: SCN-DEV-005"""
    trace = run_setpoint(
        SetpointScenario(dining_room(), ShcModel(), external_input=False), timedelta(days=2)
    )

    day_2 = trace.temperatures[MINUTES_PER_DAY:]
    assert fmean(abs(t - 20.5) for t in day_2) <= 0.5
    assert max(day_2) - 20.5 <= 0.8
    assert min(trace.valves[MINUTES_PER_DAY:]) >= 23.0  # the device's own floor
    assert trace.writes <= 2 * 48  # at most every 30 minutes on average


def test_shc_leaves_a_gap_when_the_radiator_is_tight() -> None:
    """Scenario: SCN-DEV-006"""
    room = SimRoom(floor_area_m2=20, heat_loss_w_per_k=25, rated_output_w=2000, temperature_c=19.0)

    trace = run_setpoint(
        SetpointScenario(room, ShcModel(), external_input=False), timedelta(days=3)
    )

    day_3 = trace.temperatures[2 * MINUTES_PER_DAY :]
    # Documents a device limit: without an integral part it settles below the setpoint with the
    # valve not fully open. Sending the room target cannot close the gap (ACT-056, planned).
    assert fmean(day_3) <= 20.5 - 0.8
    assert max(trace.valves[2 * MINUTES_PER_DAY :]) < 100.0
