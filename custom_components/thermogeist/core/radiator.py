# SPDX-License-Identifier: MIT
"""Radiator output and room time constant (spec MDL-012, MDL-014)."""

from __future__ import annotations

# EN 442: rated output at 75/65/20 °C, i.e. a logarithmic mean excess temperature of 49.8 K.
RATED_EXCESS_TEMPERATURE_K = 49.8
RADIATOR_EXPONENT = 1.3
# Without a return temperature we assume a typical 5 K spread: mean water = flow - 2.5 K (MDL-019).
DEFAULT_SPREAD_K = 5.0
HALF_SPREAD_K = DEFAULT_SPREAD_K / 2
# A measured spread outside this band is a sensor or hydraulic oddity, not a usable average.
SPREAD_MIN_K = 1.0
SPREAD_MAX_K = 10.0
# EN ISO 13790 "medium" construction: 165 kJ/(m²·K) ≈ 46 Wh/(m²·K) of floor area.
HEAT_CAPACITY_WH_PER_M2_K = 46.0


def usable_spread_k(flow_c: float | None, return_c: float | None) -> float | None:
    """MDL-019: measured system spread, limited to 1-10 K; None without both values."""
    if flow_c is None or return_c is None:
        return None
    return min(SPREAD_MAX_K, max(SPREAD_MIN_K, flow_c - return_c))


def available_output_w(
    rated_output_w: float,
    flow_c: float,
    room_c: float,
    spread_k: float | None = None,
    exponent: float = RADIATOR_EXPONENT,
) -> float:
    """What a fully open radiator delivers at the current flow and room temperature.

    ACT-062: heaters on the heating circuit use the same formula with their own exponent.
    """
    half_spread = HALF_SPREAD_K if spread_k is None else spread_k / 2
    excess = flow_c - half_spread - room_c
    if excess <= 0 or rated_output_w <= 0:
        return 0.0
    return rated_output_w * (excess / RATED_EXCESS_TEMPERATURE_K) ** exponent


def time_constant_h(floor_area_m2: float | None, heat_loss_w_per_k: float | None) -> float | None:
    """τ = C / H in hours, or None if either is unknown."""
    if not floor_area_m2 or not heat_loss_w_per_k:
        return None
    return floor_area_m2 * HEAT_CAPACITY_WH_PER_M2_K / heat_loss_w_per_k
