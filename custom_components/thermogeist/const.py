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
from .core.room import (
    FIELD_CEILING_HEIGHT,
    FIELD_CEILING_LOW,
    FIELD_EXTERIOR_WALLS,
    FIELD_FLOOR_AREA,
    FIELD_KNOWN_SHARE,
)

DOMAIN: Final = "thermogeist"
MANUFACTURER: Final = "Thermogeist"
DOCS_URL: Final = "https://github.com/mschmiedel/thermogeist/blob/main/docs"

# House keys. Field names come from the core so validation errors map 1:1 to inputs.
CONF_NAME: Final = FIELD_NAME
CONF_HEATING_TYPE: Final = "heating_type"
CONF_OUTDOOR_TEMPERATURE_ENTITY: Final = "outdoor_temperature_entity"
CONF_HEAT_LOAD: Final = FIELD_HEAT_LOAD
CONF_DESIGN_TEMPERATURE: Final = FIELD_DESIGN_TEMPERATURE
CONF_SHARE_OUTSIDE: Final = FIELD_SHARE_OUTSIDE
CONF_LIVING_AREA: Final = FIELD_LIVING_AREA

# Room keys.
SUBENTRY_ROOM: Final = "room"
CONF_AREA: Final = "area"
CONF_TEMPERATURE_ENTITY: Final = "temperature_entity"
CONF_SHARE_MODE: Final = "share_mode"
CONF_KNOWN_SHARE: Final = FIELD_KNOWN_SHARE
CONF_FLOOR_AREA: Final = FIELD_FLOOR_AREA
CONF_CEILING_HEIGHT: Final = FIELD_CEILING_HEIGHT
CONF_CEILING_LOW: Final = FIELD_CEILING_LOW
CONF_EXTERIOR_WALLS: Final = FIELD_EXTERIOR_WALLS
CONF_ABOVE: Final = "above"
CONF_BELOW: Final = "below"

# Room setpoint limits and default (OVR-012). 20 °C is the usual design indoor temperature.
ROOM_SETPOINT_MIN_C: Final = 5.0
ROOM_SETPOINT_MAX_C: Final = 30.0
ROOM_SETPOINT_STEP_C: Final = 0.5
ROOM_SETPOINT_DEFAULT_C: Final = 20.0

STORAGE_VERSION: Final = 1
