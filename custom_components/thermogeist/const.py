# SPDX-License-Identifier: MIT
"""Constants for the Home Assistant layer."""

from typing import Final

from .core.house import (
    FIELD_DESIGN_TEMPERATURE,
    FIELD_HEAT_LOAD,
    FIELD_LIVING_AREA,
    FIELD_NAME,
    FIELD_SHARE_OUTSIDE,
)

DOMAIN: Final = "thermogeist"
MANUFACTURER: Final = "Thermogeist"

# Config entry keys. Field names come from the core so validation errors map 1:1 to inputs.
CONF_NAME: Final = FIELD_NAME
CONF_HEATING_TYPE: Final = "heating_type"
CONF_OUTDOOR_TEMPERATURE_ENTITY: Final = "outdoor_temperature_entity"
CONF_HEAT_LOAD: Final = FIELD_HEAT_LOAD
CONF_DESIGN_TEMPERATURE: Final = FIELD_DESIGN_TEMPERATURE
CONF_SHARE_OUTSIDE: Final = FIELD_SHARE_OUTSIDE
CONF_LIVING_AREA: Final = FIELD_LIVING_AREA
