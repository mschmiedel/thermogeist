# SPDX-License-Identifier: MIT
"""Room shares of the house heat load (spec MDL-021, MDL-031, MDL-034, MDL-035).

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
        rid: room_weight(room)
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
