# SPDX-License-Identifier: MIT
"""Estimated radiator output (spec MDL-013)."""

import pytest

from custom_components.thermogeist.core.controller import feed_forward_pct
from custom_components.thermogeist.core.output import (
    RadiatorInput,
    RoomBalanceInput,
    ValveSource,
    estimate_room_output,
    house_balance,
    output_at_valve_w,
)
from custom_components.thermogeist.core.radiator import available_output_w


def test_output_follows_the_valve_characteristic() -> None:
    """Scenario: SCN-HEAT-007"""
    assert output_at_valve_w(5.0, 400.0) == 0.0
    assert output_at_valve_w(10.0, 400.0) == 0.0
    assert output_at_valve_w(55.0, 400.0) == pytest.approx(282.8, abs=0.1)
    assert output_at_valve_w(100.0, 400.0) == 400.0

    valve = feed_forward_pct(250.0, 1000.0, 50.0, 20.0)
    assert valve is not None
    available = available_output_w(1000.0, 50.0, 20.0)
    assert output_at_valve_w(valve, available) == pytest.approx(250.0)


def test_room_estimate_needs_every_radiator() -> None:
    """Scenario: SCN-HEAT-008"""
    first = RadiatorInput("A", 1000.0, 100.0, ValveSource.REPORTED)
    second = RadiatorInput("B", 500.0, 100.0, ValveSource.PLANNED)
    full = available_output_w(1000.0, 45.0, 20.0) + available_output_w(500.0, 45.0, 20.0)

    both = estimate_room_output([first, second], 45.0, 20.0, None)
    assert both.output_w == pytest.approx(full)
    assert both.max_output_w == pytest.approx(full)
    assert both.missing == ()

    no_valve = estimate_room_output(
        [first, RadiatorInput("B", 500.0, None, None)], 45.0, 20.0, None
    )
    assert no_valve.output_w is None
    assert no_valve.max_output_w == pytest.approx(full)
    assert no_valve.missing == ("valve_position",)

    no_flow = estimate_room_output([first, second], None, 20.0, None)
    assert no_flow.output_w is None
    assert no_flow.max_output_w is None
    assert no_flow.missing == ("flow_temperature",)


def test_house_balance_covers_the_same_rooms() -> None:
    """Scenario: SCN-HEAT-009"""
    balance = house_balance(
        [
            RoomBalanceInput("A", 300.0, 250.0, 100.0),
            RoomBalanceInput("B", 200.0, 150.0, None),
            RoomBalanceInput("C", 400.0, None, None),
        ]
    )

    assert balance.demand_w == 500.0
    assert balance.radiators_w == 400.0
    assert balance.devices_w == 100.0
    assert balance.rooms == 2
    assert balance.rooms_without_estimate == ("C",)
