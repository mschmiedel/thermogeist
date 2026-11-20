# SPDX-License-Identifier: MIT
"""Radiator output and room time constant (spec MDL-012, MDL-014)."""

from __future__ import annotations

# EN 442: rated output at 75/65/20 °C, i.e. a logarithmic mean excess temperature of 49.8 K.
RATED_EXCESS_TEMPERATURE_K = 49.8
RADIATOR_EXPONENT = 1.3
# Without a return temperature we assume a typical 5 K spread: mean water = flow - 2.5 K.
HALF_SPREAD_K = 2.5
# EN ISO 13790 "medium" construction: 165 kJ/(m²·K) ≈ 46 Wh/(m²·K) of floor area.
HEAT_CAPACITY_WH_PER_M2_K = 46.0


def available_output_w(rated_output_w: float, flow_c: float, room_c: float) -> float:
    """What a fully open radiator delivers at the current flow and room temperature."""
    excess = flow_c - HALF_SPREAD_K - room_c
    if excess <= 0 or rated_output_w <= 0:
        return 0.0
    return rated_output_w * (excess / RATED_EXCESS_TEMPERATURE_K) ** RADIATOR_EXPONENT


def time_constant_h(floor_area_m2: float | None, heat_loss_w_per_k: float | None) -> float | None:
    """τ = C / H in hours, or None if either is unknown."""
    if not floor_area_m2 or not heat_loss_w_per_k:
        return None
    return floor_area_m2 * HEAT_CAPACITY_WH_PER_M2_K / heat_loss_w_per_k
