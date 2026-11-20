# SPDX-License-Identifier: MIT
"""Room shares of the house heat load (spec MDL-021, MDL-031, MDL-034, MDL-035, MDL-039).

The weighting is deliberately simple and explainable; the reasons for every factor are in
spec/house-and-room-model.md. Learning will correct the estimate later (MDL-032).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .house import House
from .room import Above, Below, Room, ShareMode

REFERENCE_HEIGHT_M = 2.5
# Half of a room's loss scales with height (walls, air volume), half does not (floor, ceiling).
HEIGHT_FIXED_PART = 0.5
# Warm air collects under high ceilings: +5 % per metre above 3 m.
STRATIFICATION_FROM_M = 3.0
STRATIFICATION_PER_M = 0.05
# An interior room still loses heat (ventilation, neighbours); each exterior wall adds to it.
EXPOSURE_BASE = 0.6
EXPOSURE_PER_EXTERIOR_WALL = 0.2
EXPOSURE_ABOVE: dict[Above, float] = {Above.HEATED: 0.0, Above.UNHEATED: 0.15, Above.ROOF: 0.3}
EXPOSURE_BELOW: dict[Below, float] = {Below.HEATED: 0.0, Below.UNHEATED: 0.15, Below.GROUND: 0.1}

FULL_SHARE_PCT = 100.0
# The living-area reference assumes rooms designed for 20 °C (typical living rooms).
REFERENCE_INDOOR_C = 20.0


def height_factor(mean_height_m: float) -> float:
    """1.0 at 2.5 m; grows with height, plus a small stratification bonus."""
    proportional = (1 - HEIGHT_FIXED_PART) * mean_height_m / REFERENCE_HEIGHT_M
    stratification = STRATIFICATION_PER_M * max(0.0, mean_height_m - STRATIFICATION_FROM_M)
    return HEIGHT_FIXED_PART + proportional + stratification


def exposure_factor(room: Room) -> float:
    """1.0 for a typical room with two exterior walls and heated rooms above and below."""
    return (
        EXPOSURE_BASE
        + EXPOSURE_PER_EXTERIOR_WALL * room.exterior_walls
        + EXPOSURE_ABOVE[room.above]
        + EXPOSURE_BELOW[room.below]
    )


def temperature_factor(room: Room, house: House) -> float:
    """A room designed for 24 °C needs more than one for 20 °C. Needs the design temperature."""
    if house.design_outdoor_temperature_c is None:
        return 1.0
    reference_span = REFERENCE_INDOOR_C - house.design_outdoor_temperature_c
    if reference_span <= 0:
        return 1.0
    return (room.design_indoor_temperature_c - house.design_outdoor_temperature_c) / reference_span


def room_weight(room: Room) -> float:
    """Floor area weighted by height and exposure, in 'typical square metres'."""
    if room.floor_area_m2 is None:
        return 0.0
    return room.floor_area_m2 * height_factor(room.mean_height_m) * exposure_factor(room)


@dataclass(frozen=True, slots=True)
class ShareResult:
    """Shares per room id, the part assigned to no room, and whether estimates were scaled."""

    shares_pct: dict[str, float]
    unassigned_pct: float
    scaled_down: bool


def room_shares(house: House, rooms: Mapping[str, Room]) -> ShareResult:
    """Distribute the house heat load over the rooms."""
    known = {
        rid: room.known_share_pct or 0.0
        for rid, room in rooms.items()
        if room.share_mode is ShareMode.KNOWN
    }
    weights = {
        rid: room_weight(room) * temperature_factor(room, house)
        for rid, room in rooms.items()
        if room.share_mode is ShareMode.ESTIMATED
    }
    available = max(0.0, FULL_SHARE_PCT - house.share_outside_pct - sum(known.values()))

    if house.living_area_m2:
        estimated = {rid: FULL_SHARE_PCT * w / house.living_area_m2 for rid, w in weights.items()}
    else:
        total_weight = sum(weights.values())
        estimated = {
            rid: (available * w / total_weight if total_weight else 0.0)
            for rid, w in weights.items()
        }

    scaled_down = sum(estimated.values()) > available
    if scaled_down:
        factor = available / sum(estimated.values())
        estimated = {rid: share * factor for rid, share in estimated.items()}

    shares = known | estimated
    unassigned = FULL_SHARE_PCT - house.share_outside_pct - sum(shares.values())
    return ShareResult(
        shares_pct=shares, unassigned_pct=max(0.0, unassigned), scaled_down=scaled_down
    )


def known_shares_exceed_total(house: House, rooms: Mapping[str, Room]) -> bool:
    """MDL-021: known shares plus the share outside Thermogeist must not exceed 100 %."""
    known = sum(r.known_share_pct or 0.0 for r in rooms.values() if r.share_mode is ShareMode.KNOWN)
    return known + house.share_outside_pct > FULL_SHARE_PCT


def floor_area_not_in_rooms_m2(house: House, rooms: Mapping[str, Room]) -> float | None:
    """MDL-046: living area not yet covered by a room; None without a living area."""
    if house.living_area_m2 is None:
        return None
    in_rooms = sum(room.floor_area_m2 or 0.0 for room in rooms.values())
    return max(0.0, house.living_area_m2 - in_rooms)
