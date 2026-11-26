# SPDX-License-Identifier: MIT
"""Constants for the Home Assistant layer."""

from typing import Final

from .core.heater import (
    FIELD_EXPONENT,
    FIELD_OFF_OUTPUT,
    FIELD_STAGE_OUTPUTS,
    FIELD_STAGE_SENSOR,
    FIELD_STAGES,
)
from .core.house import (
    FIELD_CURVE_COLD_FLOW,
    FIELD_CURVE_COLD_OUTDOOR,
    FIELD_CURVE_WARM_FLOW,
    FIELD_CURVE_WARM_OUTDOOR,
    FIELD_DESIGN_TEMPERATURE,
    FIELD_HEAT_LOAD,
    FIELD_LIVING_AREA,
    FIELD_NAME,
    FIELD_SHARE_OUTSIDE,
)
from .core.room import (
    FIELD_CEILING_HEIGHT,
    FIELD_CEILING_LOW,
    FIELD_DESIGN_INDOOR,
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
CONF_FLOW_TEMPERATURE_ENTITY: Final = "flow_temperature_entity"
CONF_RETURN_TEMPERATURE_ENTITY: Final = "return_temperature_entity"
CONF_CURVE_COLD_OUTDOOR: Final = FIELD_CURVE_COLD_OUTDOOR
CONF_CURVE_COLD_FLOW: Final = FIELD_CURVE_COLD_FLOW
CONF_CURVE_WARM_OUTDOOR: Final = FIELD_CURVE_WARM_OUTDOOR
CONF_CURVE_WARM_FLOW: Final = FIELD_CURVE_WARM_FLOW

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
CONF_DESIGN_INDOOR: Final = FIELD_DESIGN_INDOOR
CONF_WINDOWS: Final = "window_sensors"
CONF_HEAT_SOURCES: Final = "heat_sources"
CONF_SOURCE_ENTITY: Final = "entity"
CONF_SOURCE_FACTOR: Final = "factor"
CONF_SOURCE_FACTOR_ENTITY: Final = "factor_entity"

# Thermostat keys.
SUBENTRY_THERMOSTAT: Final = "thermostat"
CONF_ROOM: Final = "room"
CONF_DEVICE: Final = "device"
CONF_RATED_OUTPUT: Final = "rated_output"
CONF_PROFILE: Final = "profile"
CONF_ROLES: Final = "roles"
CONF_VALVE_MIN_INVERTED: Final = "valve_min_inverted"
CONF_VALVE_REFRESH: Final = "valve_refresh_minutes"
CONF_UNCALIBRATED_VALUES: Final = "uncalibrated_values"
CONF_STRATEGY: Final = "strategy"
# HAI-007: thermostats live inside their room sub-entry, keyed by thermostat id.
CONF_THERMOSTATS: Final = "thermostats"
CONF_THERMOSTAT_NAME: Final = "name"
# Heater keys (ACT-060 to ACT-067); heaters live inside their room sub-entry like thermostats.
CONF_HEATERS: Final = "heaters"
CONF_HEATER: Final = "heater"
CONF_SWITCH: Final = "switch"
CONF_ENERGY_SOURCE: Final = "energy_source"
CONF_STAGES: Final = FIELD_STAGES
CONF_STAGE_OUTPUTS: Final = FIELD_STAGE_OUTPUTS
CONF_OFF_OUTPUT: Final = FIELD_OFF_OUTPUT
CONF_EXPONENT: Final = FIELD_EXPONENT
CONF_STAGE_SENSOR: Final = FIELD_STAGE_SENSOR
CONF_STAGE_SETTER: Final = "stage_setter"
RATED_OUTPUT_W_MIN: Final = 50.0
RATED_OUTPUT_W_MAX: Final = 10_000.0

# Room setpoint limits and default (OVR-012). 20 °C is the usual design indoor temperature.
ROOM_SETPOINT_MIN_C: Final = 5.0
ROOM_SETPOINT_MAX_C: Final = 30.0
ROOM_SETPOINT_STEP_C: Final = 0.5
ROOM_SETPOINT_DEFAULT_C: Final = 20.0

STORAGE_VERSION: Final = 1
