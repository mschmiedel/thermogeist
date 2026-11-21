# SPDX-License-Identifier: MIT
"""Heat loss and demand of a room (spec MDL-010, MDL-011, MDL-036, MDL-039, MDL-043, MDL-049)."""

from __future__ import annotations

from collections.abc import Iterable

from .house import House
from .room import HEAT_SOURCE_FACTOR_MAX_PCT, HEAT_SOURCE_FACTOR_MIN_PCT, Room

WATTS_PER_KILOWATT = 1000.0


def room_heat_loss_w_per_k(house: House, room: Room, share_pct: float) -> float | None:
    """Heat loss coefficient H of a room, or None without heat load and design temperature."""
    if house.heat_load_kw is None or house.design_outdoor_temperature_c is None:
        return None
    temperature_span = room.design_indoor_temperature_c - house.design_outdoor_temperature_c
    if temperature_span <= 0:
        return None
    room_load_w = house.heat_load_kw * WATTS_PER_KILOWATT * share_pct / 100
    return room_load_w / temperature_span


def current_demand_w(
    heat_loss_w_per_k: float | None, setpoint_c: float | None, outdoor_c: float | None
) -> float | None:
    """Heat the room needs right now to hold its setpoint. Never negative."""
    if heat_loss_w_per_k is None or setpoint_c is None or outdoor_c is None:
        return None
    return max(0.0, heat_loss_w_per_k * (setpoint_c - outdoor_c))


def effective_factor_pct(entity_value_pct: float | None, fixed_pct: float) -> float:
    """MDL-049: the factor entity wins, limited to 0-500 %; unavailable uses the fixed factor."""
    if entity_value_pct is None:
        return fixed_pct
    return min(HEAT_SOURCE_FACTOR_MAX_PCT, max(HEAT_SOURCE_FACTOR_MIN_PCT, entity_value_pct))


def heat_from_sources_w(sources: Iterable[tuple[float | None, float]]) -> float:
    """MDL-042: sum of (power in W, factor in %); unknown or negative power counts as 0."""
    return sum(max(0.0, power or 0.0) * factor_pct / 100 for power, factor_pct in sources)


def net_demand_w(demand_w: float | None, sources_w: float) -> float | None:
    """MDL-043: what the radiator still has to deliver. Never negative."""
    if demand_w is None:
        return None
    return max(0.0, demand_w - sources_w)
