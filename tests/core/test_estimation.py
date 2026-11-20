# SPDX-License-Identifier: MIT
import pytest

from custom_components.thermogeist.core.estimation import (
    exposure_factor,
    height_factor,
    known_shares_exceed_total,
    room_shares,
)
from custom_components.thermogeist.core.house import HeatingType, House
from custom_components.thermogeist.core.room import Above, Below, Room, ShareMode

HOUSE = House(
    name="Home",
    heating_type=HeatingType.HEAT_PUMP,
    outdoor_temperature_entity="sensor.outdoor",
    living_area_m2=160.0,
)


def typical(area: float) -> Room:
    """2.5 m, two exterior walls, heated above and below: both factors 1.0."""
    return Room(name="Room", temperature_entity="sensor.t", floor_area_m2=area, exterior_walls=2)


def known(share: float) -> Room:
    return Room(
        name="Room",
        temperature_entity="sensor.t",
        share_mode=ShareMode.KNOWN,
        known_share_pct=share,
    )


def test_typical_room_matches_area_share() -> None:
    """Scenario: SCN-SHARE-001"""
    result = room_shares(HOUSE, {"a": typical(20.0)})
    assert result.shares_pct["a"] == pytest.approx(12.5)
    assert result.unassigned_pct == pytest.approx(87.5)
    assert not result.scaled_down


def test_height_and_exposure_change_the_weight() -> None:
    """Scenario: SCN-SHARE-002"""
    living = Room(
        name="Living",
        temperature_entity="sensor.t",
        floor_area_m2=40.0,
        ceiling_height_m=3.5,
        exterior_walls=3,
        below=Below.GROUND,
    )
    attic = Room(
        name="Attic",
        temperature_entity="sensor.t",
        floor_area_m2=15.0,
        ceiling_height_m=2.8,
        ceiling_low_m=1.2,
        exterior_walls=2,
        above=Above.ROOF,
    )
    assert height_factor(living.mean_height_m) == pytest.approx(1.225)
    assert exposure_factor(living) == pytest.approx(1.3)
    assert height_factor(attic.mean_height_m) == pytest.approx(0.9)
    assert exposure_factor(attic) == pytest.approx(1.3)

    result = room_shares(HOUSE, {"living": living, "attic": attic})
    assert result.shares_pct["living"] == pytest.approx(39.8125)
    assert result.shares_pct["attic"] == pytest.approx(10.96875)


def test_without_living_area_estimated_rooms_share_the_rest() -> None:
    """Scenario: SCN-SHARE-003"""
    house = House(
        name="Home",
        heating_type=HeatingType.HEAT_PUMP,
        outdoor_temperature_entity="sensor.outdoor",
        share_outside_pct=10.0,
    )
    result = room_shares(house, {"k": known(30.0), "a": typical(20.0), "b": typical(10.0)})
    assert result.shares_pct == pytest.approx({"k": 30.0, "a": 40.0, "b": 20.0})
    assert result.unassigned_pct == pytest.approx(0.0)


def test_estimates_above_available_are_scaled() -> None:
    """Scenario: SCN-SHARE-004"""
    house = House(
        name="Home",
        heating_type=HeatingType.HEAT_PUMP,
        outdoor_temperature_entity="sensor.outdoor",
        living_area_m2=50.0,
    )
    result = room_shares(house, {"a": typical(40.0), "b": typical(30.0)})
    assert result.shares_pct["a"] == pytest.approx(100 * 4 / 7)
    assert result.shares_pct["b"] == pytest.approx(100 * 3 / 7)
    assert result.scaled_down
    assert result.unassigned_pct == pytest.approx(0.0)


def test_known_shares_exceeding_total_are_detected() -> None:
    """Scenario: SCN-SHARE-005"""
    house = House(
        name="Home",
        heating_type=HeatingType.HEAT_PUMP,
        outdoor_temperature_entity="sensor.outdoor",
        share_outside_pct=10.0,
    )
    assert known_shares_exceed_total(house, {"a": known(60.0), "b": known(35.0)})
    assert not known_shares_exceed_total(house, {"a": known(55.0), "b": known(35.0)})


def test_bathroom_design_temperature_raises_share() -> None:
    """Scenario: SCN-SHARE-006"""
    house = House(
        name="Home",
        heating_type=HeatingType.HEAT_PUMP,
        outdoor_temperature_entity="sensor.outdoor",
        living_area_m2=160.0,
        design_outdoor_temperature_c=-10.5,
    )
    bath = Room(
        name="Bath",
        temperature_entity="sensor.t",
        floor_area_m2=8.0,
        exterior_walls=2,
        design_indoor_temperature_c=24.0,
    )
    assert room_shares(house, {"b": bath}).shares_pct["b"] == pytest.approx(5.0 * 34.5 / 30.5)

    without_design = House(
        name="Home",
        heating_type=HeatingType.HEAT_PUMP,
        outdoor_temperature_entity="sensor.outdoor",
        living_area_m2=160.0,
    )
    assert room_shares(without_design, {"b": bath}).shares_pct["b"] == pytest.approx(5.0)
