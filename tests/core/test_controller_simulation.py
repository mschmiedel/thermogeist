# SPDX-License-Identifier: MIT
"""Closed-loop tests: real controller against the room simulator (spec TST-013, TST-030)."""

from datetime import timedelta

from custom_components.thermogeist.core.controller import ControllerSettings
from tests.sim import metrics
from tests.sim.room import SimRoom
from tests.sim.run import Scenario, run

DAYS_4 = timedelta(days=4)
DAY_3 = (48.0, 72.0)


def living_room(start_c: float = 19.0) -> SimRoom:
    """20 m², 20 W/K, 2 kW radiator (75/65/20): at 40 °C flow it just covers 0 °C outdoors."""
    return SimRoom(
        floor_area_m2=20, heat_loss_w_per_k=20, rated_output_w=2000, temperature_c=start_c
    )


def test_heat_pump_with_full_data_is_calm_and_open() -> None:
    """Scenario: SCN-CTL-001"""
    trace = run(Scenario(living_room()), DAYS_4)

    assert metrics.overshoot_k(trace, 20.0) <= 0.4
    settling = metrics.settling_time_h(trace, 20.0)
    assert settling is not None and settling <= 16
    assert metrics.valve_moves(trace, *DAY_3) <= 10
    assert metrics.mean_opening_pct(trace, *DAY_3) >= 40
    assert min(trace.outputs) >= 40


def test_feedback_only_still_reaches_target() -> None:
    """Scenario: SCN-CTL-002"""
    trace = run(Scenario(living_room(), knows_heat_loss=False), DAYS_4)

    assert metrics.overshoot_k(trace, 20.0) <= 0.3
    settling = metrics.settling_time_h(trace, 20.0)
    assert settling is not None and settling <= 36
    assert metrics.valve_moves(trace, *DAY_3) <= 10


def test_valve_never_moves_faster_than_allowed() -> None:
    """Scenario: SCN-CTL-003"""
    trace = run(Scenario(living_room(start_c=17.0)), DAYS_4)

    window = 30
    for start in range(1, len(trace.outputs) - window):
        assert abs(trace.outputs[start + window] - trace.outputs[start]) <= 10 + 1


def test_boiler_profile_reacts_faster() -> None:
    """Scenario: SCN-CTL-004"""
    boiler = ControllerSettings(min_opening_pct=0.0, dead_band_k=0.2, max_change_pct_per_30min=30.0)
    trace = run(Scenario(living_room(), flow_c=60.0, settings=boiler), DAYS_4)

    settling = metrics.settling_time_h(trace, 20.0)
    assert settling is not None and settling <= 4
    assert metrics.overshoot_k(trace, 20.0) <= 0.4


def test_oversized_radiator_relaxes_minimum_opening() -> None:
    """Scenario: SCN-CTL-005"""
    bathroom = SimRoom(
        floor_area_m2=3, heat_loss_w_per_k=4.3, rated_output_w=1000, temperature_c=19.0
    )
    trace = run(Scenario(bathroom, outdoor_c=5.0, flow_c=35.0), DAYS_4)

    day_3 = range(int(DAY_3[0] * 60), int(DAY_3[1] * 60))
    assert max(trace.temperatures[i] for i in day_3) <= 21.1
    assert any("min_opening_relaxed" in r.limits for r in trace.results)
    assert min(trace.outputs[i] for i in day_3) < 40
