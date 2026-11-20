# SPDX-License-Identifier: MIT
"""Translate between config entry data and the core house model."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_DESIGN_TEMPERATURE,
    CONF_HEAT_LOAD,
    CONF_HEATING_TYPE,
    CONF_LIVING_AREA,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_SHARE_OUTSIDE,
)
from .core.house import HeatingType, House


def house_from_config(config: Mapping[str, Any]) -> House:
    """Build a house from flow input or stored entry data."""
    return House(
        name=str(config.get(CONF_NAME, "")),
        heating_type=HeatingType(config[CONF_HEATING_TYPE]),
        outdoor_temperature_entity=str(config.get(CONF_OUTDOOR_TEMPERATURE_ENTITY, "")),
        heat_load_kw=_optional_float(config.get(CONF_HEAT_LOAD)),
        design_outdoor_temperature_c=_optional_float(config.get(CONF_DESIGN_TEMPERATURE)),
        share_outside_pct=_optional_float(config.get(CONF_SHARE_OUTSIDE)) or 0.0,
        living_area_m2=_optional_float(config.get(CONF_LIVING_AREA)),
    )


def house_from_entry(entry: ConfigEntry) -> House:
    """The effective house: stored data, overridden by later changes in the options."""
    return house_from_config({**entry.data, **entry.options})


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
