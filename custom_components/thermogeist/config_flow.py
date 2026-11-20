# SPDX-License-Identifier: MIT
"""Setup and options dialogs for a house (spec HAI-001 to HAI-003)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import PERCENTAGE, UnitOfArea, UnitOfPower, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_DESIGN_TEMPERATURE,
    CONF_HEAT_LOAD,
    CONF_HEATING_TYPE,
    CONF_LIVING_AREA,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_SHARE_OUTSIDE,
    DOMAIN,
)
from .core.house import (
    DESIGN_TEMP_C_MAX,
    DESIGN_TEMP_C_MIN,
    HEAT_LOAD_KW_MAX,
    HEAT_LOAD_KW_MIN,
    LIVING_AREA_M2_MAX,
    LIVING_AREA_M2_MIN,
    SHARE_PCT_MAX,
    SHARE_PCT_MIN,
    HeatingType,
    validate_house,
)
from .house_config import house_from_config

DETAIL_KEYS = (CONF_HEAT_LOAD, CONF_DESIGN_TEMPERATURE, CONF_SHARE_OUTSIDE, CONF_LIVING_AREA)


def _number(minimum: float, maximum: float, step: float, unit: str) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            unit_of_measurement=unit,
            mode=NumberSelectorMode.BOX,
        )
    )


def _required_schema(
    defaults: Mapping[str, Any], *, include_name: bool = True
) -> dict[vol.Marker, Any]:
    name_field: dict[vol.Marker, Any] = (
        {vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, vol.UNDEFINED)): TextSelector()}
        if include_name
        else {}
    )
    return name_field | {
        vol.Required(
            CONF_HEATING_TYPE,
            default=defaults.get(CONF_HEATING_TYPE, HeatingType.HEAT_PUMP.value),
        ): SelectSelector(
            SelectSelectorConfig(
                options=[t.value for t in HeatingType],
                translation_key=CONF_HEATING_TYPE,
                mode=SelectSelectorMode.LIST,
            )
        ),
        vol.Required(
            CONF_OUTDOOR_TEMPERATURE_ENTITY,
            default=defaults.get(CONF_OUTDOOR_TEMPERATURE_ENTITY, vol.UNDEFINED),
        ): EntitySelector(
            EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.TEMPERATURE)
        ),
    }


def _detail_schema(defaults: Mapping[str, Any]) -> dict[vol.Marker, Any]:
    def optional(key: str) -> vol.Optional:
        value = defaults.get(key)
        return vol.Optional(
            key, description={"suggested_value": value} if value is not None else None
        )

    return {
        optional(CONF_HEAT_LOAD): _number(
            HEAT_LOAD_KW_MIN, HEAT_LOAD_KW_MAX, 0.1, UnitOfPower.KILO_WATT
        ),
        optional(CONF_DESIGN_TEMPERATURE): _number(
            DESIGN_TEMP_C_MIN, DESIGN_TEMP_C_MAX, 0.5, UnitOfTemperature.CELSIUS
        ),
        optional(CONF_SHARE_OUTSIDE): _number(SHARE_PCT_MIN, SHARE_PCT_MAX, 1, PERCENTAGE),
        optional(CONF_LIVING_AREA): _number(
            LIVING_AREA_M2_MIN, LIVING_AREA_M2_MAX, 1, UnitOfArea.SQUARE_METERS
        ),
    }


def _errors(config: Mapping[str, Any]) -> dict[str, str]:
    """Validate with the core and map issues to form fields."""
    return {issue.field: issue.code for issue in validate_house(house_from_config(config))}


class ThermogeistConfigFlow(ConfigFlow, domain=DOMAIN):
    """Two steps: required answers, then optional details."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _errors(user_input)
            if not errors:
                self._data = dict(user_input)
                return await self.async_step_details()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(_required_schema(user_input or {})),
            errors=errors,
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {**self._data, **user_input}
            errors = _errors(candidate)
            if not errors:
                return self.async_create_entry(title=candidate[CONF_NAME].strip(), data=candidate)
        return self.async_show_form(
            step_id="details",
            data_schema=vol.Schema(_detail_schema(user_input or {})),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ThermogeistOptionsFlow()


class ThermogeistOptionsFlow(OptionsFlow):
    """Change every house setting later (HAI-003). The name stays the entry title."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {CONF_NAME: current[CONF_NAME], **user_input}
            errors = _errors(candidate)
            if not errors:
                # Optional fields left empty must clear older values.
                options = {key: user_input.get(key) for key in DETAIL_KEYS} | {
                    CONF_HEATING_TYPE: user_input[CONF_HEATING_TYPE],
                    CONF_OUTDOOR_TEMPERATURE_ENTITY: user_input[CONF_OUTDOOR_TEMPERATURE_ENTITY],
                }
                return self.async_create_entry(data=options)
        defaults = user_input or current
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                _required_schema(defaults, include_name=False) | _detail_schema(defaults)
            ),
            errors=errors,
        )
