# SPDX-License-Identifier: MIT
"""Room description and its validation (spec MDL-004, MDL-030, MDL-033, MDL-039)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .house import ValidationIssue


class ShareMode(StrEnum):
    """How the room's share of the heat load is obtained (MDL-030, MDL-031)."""

    ESTIMATED = "estimated"
    KNOWN = "known"


class Above(StrEnum):
    """What is above the room."""

    HEATED = "heated"
    UNHEATED = "unheated"
    ROOF = "roof"


class Below(StrEnum):
    """What is below the room."""

    HEATED = "heated"
    UNHEATED = "unheated"
    GROUND = "ground"


DEFAULT_CEILING_HEIGHT_M = 2.5
# MDL-039: EN 12831 uses 20 °C for living rooms, 24 °C for bathrooms, 15 °C for heated halls.
DEFAULT_DESIGN_INDOOR_C = 20.0
DESIGN_INDOOR_C_MIN = 10.0
DESIGN_INDOOR_C_MAX = 30.0
DEFAULT_EXTERIOR_WALLS = 1
FLOOR_AREA_M2_MIN = 1.0
FLOOR_AREA_M2_MAX = 500.0
CEILING_M_MIN = 1.0
CEILING_M_MAX = 12.0
EXTERIOR_WALLS_MIN = 0
EXTERIOR_WALLS_MAX = 4
KNOWN_SHARE_PCT_MIN = 0.0
KNOWN_SHARE_PCT_MAX = 100.0

FIELD_ROOM_NAME = "name"
FIELD_KNOWN_SHARE = "known_share"
FIELD_FLOOR_AREA = "floor_area"
FIELD_CEILING_HEIGHT = "ceiling_height"
FIELD_CEILING_LOW = "ceiling_low"
FIELD_EXTERIOR_WALLS = "exterior_walls"
FIELD_DESIGN_INDOOR = "design_indoor_temperature"


@dataclass(frozen=True, slots=True)
class Room:
    """Everything the user tells Thermogeist about one room."""

    name: str
    temperature_entity: str
    share_mode: ShareMode = ShareMode.ESTIMATED
    known_share_pct: float | None = None
    floor_area_m2: float | None = None
    ceiling_height_m: float = DEFAULT_CEILING_HEIGHT_M
    ceiling_low_m: float | None = None
    exterior_walls: int = DEFAULT_EXTERIOR_WALLS
    above: Above = Above.HEATED
    below: Below = Below.HEATED
    design_indoor_temperature_c: float = DEFAULT_DESIGN_INDOOR_C
    """Planning value only (MDL-039); the setpoint decides how warm the room is heated."""

    @property
    def mean_height_m(self) -> float:
        """Mean ceiling height; with a sloped ceiling the mean of lowest and highest point."""
        if self.ceiling_low_m is None:
            return self.ceiling_height_m
        return (self.ceiling_low_m + self.ceiling_height_m) / 2


def validate_room(room: Room) -> list[ValidationIssue]:
    """Return all problems with the room description. An empty list means valid."""
    issues: list[ValidationIssue] = []
    if not room.name.strip():
        issues.append(ValidationIssue(FIELD_ROOM_NAME, "name_empty"))
    if (issue := validate_design_indoor(room.design_indoor_temperature_c)) is not None:
        issues.append(issue)
    if room.share_mode is ShareMode.KNOWN:
        _required_in_range(
            issues,
            FIELD_KNOWN_SHARE,
            room.known_share_pct,
            KNOWN_SHARE_PCT_MIN,
            KNOWN_SHARE_PCT_MAX,
        )
        return issues
    _required_in_range(
        issues, FIELD_FLOOR_AREA, room.floor_area_m2, FLOOR_AREA_M2_MIN, FLOOR_AREA_M2_MAX
    )
    _required_in_range(
        issues, FIELD_CEILING_HEIGHT, room.ceiling_height_m, CEILING_M_MIN, CEILING_M_MAX
    )
    if room.ceiling_low_m is not None:
        if not CEILING_M_MIN <= room.ceiling_low_m <= CEILING_M_MAX:
            issues.append(ValidationIssue(FIELD_CEILING_LOW, "ceiling_low_out_of_range"))
        elif room.ceiling_low_m > room.ceiling_height_m:
            issues.append(ValidationIssue(FIELD_CEILING_LOW, "ceiling_low_above_height"))
    if not EXTERIOR_WALLS_MIN <= room.exterior_walls <= EXTERIOR_WALLS_MAX:
        issues.append(ValidationIssue(FIELD_EXTERIOR_WALLS, "exterior_walls_out_of_range"))
    return issues


def validate_design_indoor(value: float) -> ValidationIssue | None:
    """Range check for the design indoor temperature, usable on its own in the room dialog."""
    if DESIGN_INDOOR_C_MIN <= value <= DESIGN_INDOOR_C_MAX:
        return None
    return ValidationIssue(FIELD_DESIGN_INDOOR, "design_indoor_temperature_out_of_range")


def _required_in_range(
    issues: list[ValidationIssue],
    field: str,
    value: float | None,
    minimum: float,
    maximum: float,
) -> None:
    if value is None:
        issues.append(ValidationIssue(field, f"{field}_required"))
    elif not minimum <= value <= maximum:
        issues.append(ValidationIssue(field, f"{field}_out_of_range"))
