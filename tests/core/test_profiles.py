# SPDX-License-Identifier: MIT
from custom_components.thermogeist.core.house import HeatingType
from custom_components.thermogeist.core.profiles import (
    ControlSetting,
    EffectiveSetting,
    Profile,
    SettingSource,
    effective_settings,
    is_valid_override,
    profile_for,
)


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


def test_overrides_win_and_survive_heating_type_change() -> None:
    """Scenario: SCN-HOUSE-006"""
    overrides = {ControlSetting.MIN_VALVE_OPENING: 30.0}

    heat_pump = effective_settings(HeatingType.HEAT_PUMP, overrides)
    assert heat_pump[ControlSetting.MIN_VALVE_OPENING] == EffectiveSetting(30.0, SettingSource.USER)
    assert heat_pump[ControlSetting.DEAD_BAND] == EffectiveSetting(0.5, SettingSource.PROFILE)

    boiler = effective_settings(HeatingType.BOILER, overrides)
    assert boiler[ControlSetting.MIN_VALVE_OPENING] == EffectiveSetting(30.0, SettingSource.USER)
    assert boiler[ControlSetting.DEAD_BAND] == EffectiveSetting(0.2, SettingSource.PROFILE)

    reset = effective_settings(HeatingType.BOILER, {})
    assert reset[ControlSetting.MIN_VALVE_OPENING] == EffectiveSetting(0.0, SettingSource.PROFILE)


def test_override_limits() -> None:
    assert is_valid_override(ControlSetting.DEAD_BAND, 2.0)
    assert not is_valid_override(ControlSetting.DEAD_BAND, 2.1)
    assert not is_valid_override(ControlSetting.MAX_VALVE_CHANGE, 0.0)
