# SPDX-License-Identifier: MIT
"""Controller profile defaults per heating type (spec CTL-010 to CTL-013).

The values are provisional until the controller is tuned with the simulator (M3).
The reasons for each value are documented in spec/controller.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from .house import HeatingType


@dataclass(frozen=True, slots=True)
class Profile:
    """Default control behaviour implied by the heating type."""

    min_valve_opening_pct: float
    dead_band_k: float
    max_valve_change_pct_per_30min: float
    max_setback_k: float


PROFILES: dict[HeatingType, Profile] = {
    HeatingType.HEAT_PUMP: Profile(
        min_valve_opening_pct=40.0,
        dead_band_k=0.5,
        max_valve_change_pct_per_30min=10.0,
        max_setback_k=2.0,
    ),
    HeatingType.BOILER: Profile(
        min_valve_opening_pct=0.0,
        dead_band_k=0.2,
        max_valve_change_pct_per_30min=30.0,
        max_setback_k=4.0,
    ),
    HeatingType.DIRECT_ELECTRIC: Profile(
        min_valve_opening_pct=0.0,
        dead_band_k=0.2,
        max_valve_change_pct_per_30min=100.0,
        max_setback_k=4.0,
    ),
}


def profile_for(heating_type: HeatingType) -> Profile:
    """Return the default profile for a heating type."""
    return PROFILES[heating_type]
