# SPDX-License-Identifier: MIT
"""Thermal model of one room with a radiator and a thermostatic valve (spec TST-010, TST-011)."""

from __future__ import annotations

from dataclasses import dataclass

from custom_components.thermogeist.core.radiator import (
    HEAT_CAPACITY_WH_PER_M2_K,
    available_output_w,
)


@dataclass
class SimRoom:
    """Single-node room: dT/dt = (radiator + gains - H x (T - outdoor)) / C."""

    floor_area_m2: float
    heat_loss_w_per_k: float
    rated_output_w: float
    temperature_c: float
    opening_point_pct: float = 10.0
    """Below this valve position no water flows (TST-011)."""

    @property
    def capacity_wh_per_k(self) -> float:
        return self.floor_area_m2 * HEAT_CAPACITY_WH_PER_M2_K

    def valve_fraction(self, valve_pct: float) -> float:
        """Concave characteristic: output rises steeply right after the opening point."""
        if valve_pct <= self.opening_point_pct:
            return 0.0
        return ((valve_pct - self.opening_point_pct) / (100.0 - self.opening_point_pct)) ** 0.5

    def radiator_w(self, valve_pct: float, flow_c: float) -> float:
        return self.valve_fraction(valve_pct) * available_output_w(
            self.rated_output_w, flow_c, self.temperature_c
        )

    def step(
        self, valve_pct: float, outdoor_c: float, flow_c: float, gains_w: float, minutes: float
    ) -> None:
        heat_w = (
            self.radiator_w(valve_pct, flow_c)
            + gains_w
            - self.heat_loss_w_per_k * (self.temperature_c - outdoor_c)
        )
        self.temperature_c += heat_w * (minutes / 60) / self.capacity_wh_per_k
