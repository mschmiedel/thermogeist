# SPDX-License-Identifier: MIT
from custom_components.thermogeist.core.house import HeatingType
from custom_components.thermogeist.core.profiles import Profile, profile_for


def test_profile_defaults_per_heating_type() -> None:
    """Scenario: SCN-HOUSE-004"""
    assert profile_for(HeatingType.HEAT_PUMP) == Profile(
        min_valve_opening_pct=40.0,
        dead_band_k=0.5,
        max_valve_change_pct_per_30min=10.0,
        max_setback_k=2.0,
    )
    assert profile_for(HeatingType.BOILER) == Profile(
        min_valve_opening_pct=0.0,
        dead_band_k=0.2,
        max_valve_change_pct_per_30min=30.0,
        max_setback_k=4.0,
    )
    assert profile_for(HeatingType.DIRECT_ELECTRIC) == Profile(
        min_valve_opening_pct=0.0,
        dead_band_k=0.2,
        max_valve_change_pct_per_30min=100.0,
        max_setback_k=4.0,
    )
