# SPDX-License-Identifier: MIT
from dataclasses import replace

from custom_components.thermogeist.core.house import ValidationIssue
from custom_components.thermogeist.core.room import Room, ShareMode, validate_room

OFFICE = Room(name="Office", temperature_entity="sensor.office")


def test_estimated_room_needs_floor_area() -> None:
    """Scenario: SCN-ROOM-001"""
    assert validate_room(OFFICE) == [ValidationIssue("floor_area", "floor_area_required")]

    room = replace(OFFICE, floor_area_m2=12.0)
    assert validate_room(room) == []
    assert room.ceiling_height_m == 2.5
    assert room.exterior_walls == 1


def test_sloped_ceiling_uses_mean_height() -> None:
    """Scenario: SCN-ROOM-002"""
    attic = replace(OFFICE, floor_area_m2=15.0, ceiling_height_m=2.8, ceiling_low_m=1.2)
    assert validate_room(attic) == []
    assert attic.mean_height_m == 2.0

    swapped = replace(attic, ceiling_low_m=3.0)
    assert validate_room(swapped) == [ValidationIssue("ceiling_low", "ceiling_low_above_height")]


def test_known_share_is_required_and_checked() -> None:
    """Scenario: SCN-ROOM-003"""
    known = replace(OFFICE, share_mode=ShareMode.KNOWN)
    assert validate_room(known) == [ValidationIssue("known_share", "known_share_required")]
    assert validate_room(replace(known, known_share_pct=120.0)) == [
        ValidationIssue("known_share", "known_share_out_of_range")
    ]
    assert validate_room(replace(known, known_share_pct=14.5)) == []


def test_design_indoor_temperature_is_checked_in_both_modes() -> None:
    """Scenario: SCN-ROOM-004"""
    estimated = replace(OFFICE, floor_area_m2=8.0, design_indoor_temperature_c=24.0)
    assert validate_room(estimated) == []
    assert validate_room(replace(estimated, design_indoor_temperature_c=35.0)) == [
        ValidationIssue("design_indoor_temperature", "design_indoor_temperature_out_of_range")
    ]
    known = replace(
        OFFICE, share_mode=ShareMode.KNOWN, known_share_pct=5.0, design_indoor_temperature_c=9.0
    )
    assert validate_room(known) == [
        ValidationIssue("design_indoor_temperature", "design_indoor_temperature_out_of_range")
    ]
