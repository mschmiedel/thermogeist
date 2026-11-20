# SPDX-License-Identifier: MIT
"""Heat loss and current demand of a room (spec MDL-010, MDL-011, MDL-036)."""

from __future__ import annotations

from .house import House

# Heat load calculations (EN 12831) are usually done for 20 °C indoors.
DESIGN_INDOOR_TEMP_C = 20.0
WATTS_PER_KILOWATT = 1000.0


def room_heat_loss_w_per_k(house: House, share_pct: float) -> float | None:
    """Heat loss coefficient H of a room, or None without heat load and design temperature."""
    if house.heat_load_kw is None or house.design_outdoor_temperature_c is None:
        return None
    temperature_span = DESIGN_INDOOR_TEMP_C - house.design_outdoor_temperature_c
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
