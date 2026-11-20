# SPDX-License-Identifier: MIT
"""Heat loss and current demand of a room (spec MDL-010, MDL-011, MDL-036, MDL-039)."""

from __future__ import annotations

from .house import House
from .room import Room

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
