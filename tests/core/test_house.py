# SPDX-License-Identifier: MIT
from dataclasses import replace

import pytest

from custom_components.thermogeist.core.house import (
    FIELD_CURVE_COLD_FLOW,
    FIELD_CURVE_WARM_FLOW,
    FIELD_CURVE_WARM_OUTDOOR,
    FIELD_DESIGN_TEMPERATURE,
    FIELD_HEAT_LOAD,
    FIELD_LIVING_AREA,
    FIELD_NAME,
    FIELD_SHARE_OUTSIDE,
    CurvePoints,
    HeatingType,
    House,
    ValidationIssue,
    validate_house,
)

MINIMAL = House(
    name="Home",
    heating_type=HeatingType.HEAT_PUMP,
    outdoor_temperature_entity="sensor.outdoor",
)


def test_minimal_house_is_valid() -> None:
    """Scenario: SCN-HOUSE-001"""
    assert validate_house(MINIMAL) == []
    assert MINIMAL.share_outside_pct == 0.0


def test_heat_load_requires_design_temperature() -> None:
    """Scenario: SCN-HOUSE-002"""
    with_load = replace(MINIMAL, heat_load_kw=8.0)
    assert validate_house(with_load) == [
        ValidationIssue(FIELD_DESIGN_TEMPERATURE, "design_temperature_required")
    ]

    complete = replace(with_load, design_outdoor_temperature_c=-12.0)
    assert validate_house(complete) == []


WITH_DESIGN_TEMP = replace(MINIMAL, design_outdoor_temperature_c=-12.0)

EDGES = [
    ("heat_load_kw", FIELD_HEAT_LOAD, [0.5, 100.0], [0.4, 100.1]),
    ("design_outdoor_temperature_c", FIELD_DESIGN_TEMPERATURE, [-40.0, 10.0], [-40.1, 10.1]),
    ("share_outside_pct", FIELD_SHARE_OUTSIDE, [0.0, 100.0], [-0.1, 100.1]),
    ("living_area_m2", FIELD_LIVING_AREA, [10.0, 10_000.0], [9.9, 10_000.1]),
]


@pytest.mark.parametrize(("attribute", "field", "inside", "outside"), EDGES)
def test_limits_are_checked_at_both_edges(
    attribute: str, field: str, inside: list[float], outside: list[float]
) -> None:
    """Scenario: SCN-HOUSE-003"""
    for value in inside:
        assert validate_house(replace(WITH_DESIGN_TEMP, **{attribute: value})) == []
    for value in outside:
        assert validate_house(replace(WITH_DESIGN_TEMP, **{attribute: value})) == [
            ValidationIssue(field, f"{field}_out_of_range")
        ]


def test_blank_name_is_rejected() -> None:
    """Scenario: SCN-HOUSE-005"""
    assert validate_house(replace(MINIMAL, name="   ")) == [
        ValidationIssue(FIELD_NAME, "name_empty")
    ]


CURVE = CurvePoints(cold_outdoor_c=-10.0, cold_flow_c=45.0, warm_outdoor_c=15.0, warm_flow_c=30.0)


def test_heating_curve_from_two_points() -> None:
    """Scenario: SCN-HOUSE-011"""
    assert CURVE.flow_at(-10.0) == 45.0
    assert CURVE.flow_at(5.0) == pytest.approx(36.0)
    assert CURVE.flow_at(15.0) == 30.0
    # Beyond the points the heat generator holds its limits.
    assert CURVE.flow_at(-20.0) == 45.0
    assert CURVE.flow_at(20.0) == 30.0
    assert validate_house(replace(MINIMAL, heating_curve=CURVE)) == []


@pytest.mark.parametrize(
    ("curve", "issue"),
    [
        (
            replace(CURVE, warm_outdoor_c=-10.0),
            ValidationIssue(FIELD_CURVE_WARM_OUTDOOR, "curve_warm_not_above_cold"),
        ),
        (
            replace(CURVE, warm_flow_c=50.0),
            ValidationIssue(FIELD_CURVE_WARM_FLOW, "curve_flow_rises_when_warmer"),
        ),
        (
            replace(CURVE, cold_flow_c=95.0),
            ValidationIssue(FIELD_CURVE_COLD_FLOW, "curve_cold_flow_out_of_range"),
        ),
    ],
)
def test_implausible_heating_curve_is_rejected(curve: CurvePoints, issue: ValidationIssue) -> None:
    """Scenario: SCN-HOUSE-012"""
    assert validate_house(replace(MINIMAL, heating_curve=curve)) == [issue]
