# SPDX-License-Identifier: MIT
"""Controller profile defaults per heating type and user overrides (spec CTL-010 to CTL-014).

The default values are provisional until the controller is tuned with the simulator (M3).
The reasons for each value are documented in spec/controller.md.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .decisions import WINDOW_DELAY_MAX, WINDOW_OPEN_AFTER, WINDOW_RESUME_AFTER
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


class ControlSetting(StrEnum):
    """Control settings the user may override (CTL-014)."""

    MIN_VALVE_OPENING = "min_valve_opening"
    DEAD_BAND = "dead_band"
    MAX_VALVE_CHANGE = "max_valve_change"
    MAX_SETBACK = "max_setback"
    WINDOW_CLOSE_AFTER = "window_close_after"
    WINDOW_RESUME_AFTER = "window_resume_after"


WINDOW_SETTINGS = (ControlSetting.WINDOW_CLOSE_AFTER, ControlSetting.WINDOW_RESUME_AFTER)
"""RUL-014: also settable per room."""


class SettingSource(StrEnum):
    """Where an effective value comes from (RUL-002)."""

    PROFILE = "profile"
    USER = "user"


@dataclass(frozen=True, slots=True)
class SettingLimits:
    minimum: float
    maximum: float
    step: float


# Allowed ranges for overrides. A dead band above 2 K or a setback above 6 K would defeat the
# purpose of room control; a max. change below 1 % per 30 min would freeze the valve.
LIMITS: dict[ControlSetting, SettingLimits] = {
    ControlSetting.MIN_VALVE_OPENING: SettingLimits(0.0, 100.0, 1.0),
    ControlSetting.DEAD_BAND: SettingLimits(0.0, 2.0, 0.1),
    ControlSetting.MAX_VALVE_CHANGE: SettingLimits(1.0, 100.0, 1.0),
    ControlSetting.MAX_SETBACK: SettingLimits(0.0, 6.0, 0.5),
    ControlSetting.WINDOW_CLOSE_AFTER: SettingLimits(0.0, WINDOW_DELAY_MAX.total_seconds(), 1.0),
    ControlSetting.WINDOW_RESUME_AFTER: SettingLimits(0.0, WINDOW_DELAY_MAX.total_seconds(), 1.0),
}


@dataclass(frozen=True, slots=True)
class EffectiveSetting:
    value: float
    source: SettingSource


def profile_value(profile: Profile, setting: ControlSetting) -> float:
    """Read one setting from a profile."""
    return {
        ControlSetting.MIN_VALVE_OPENING: profile.min_valve_opening_pct,
        ControlSetting.DEAD_BAND: profile.dead_band_k,
        ControlSetting.MAX_VALVE_CHANGE: profile.max_valve_change_pct_per_30min,
        ControlSetting.MAX_SETBACK: profile.max_setback_k,
        # RUL-014: the same for every heating type.
        ControlSetting.WINDOW_CLOSE_AFTER: WINDOW_OPEN_AFTER.total_seconds(),
        ControlSetting.WINDOW_RESUME_AFTER: WINDOW_RESUME_AFTER.total_seconds(),
    }[setting]


def effective_settings(
    heating_type: HeatingType, overrides: Mapping[ControlSetting, float]
) -> dict[ControlSetting, EffectiveSetting]:
    """Overrides win; everything else follows the profile of the heating type."""
    profile = profile_for(heating_type)
    return {
        setting: (
            EffectiveSetting(overrides[setting], SettingSource.USER)
            if setting in overrides
            else EffectiveSetting(profile_value(profile, setting), SettingSource.PROFILE)
        )
        for setting in ControlSetting
    }


def is_valid_override(setting: ControlSetting, value: float) -> bool:
    limits = LIMITS[setting]
    return limits.minimum <= value <= limits.maximum
