# SPDX-License-Identifier: MIT
"""Setup and options dialogs for a house and its rooms (spec HAI-001 to HAI-005)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import PERCENTAGE, UnitOfArea, UnitOfPower, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    AreaSelector,
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
    CONF_ABOVE,
    CONF_AREA,
    CONF_BELOW,
    CONF_CEILING_HEIGHT,
    CONF_CEILING_LOW,
    CONF_DESIGN_INDOOR,
    CONF_DESIGN_TEMPERATURE,
    CONF_EXTERIOR_WALLS,
    CONF_FLOOR_AREA,
    CONF_HEAT_LOAD,
    CONF_HEATING_TYPE,
    CONF_KNOWN_SHARE,
    CONF_LIVING_AREA,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_SHARE_MODE,
    CONF_SHARE_OUTSIDE,
    CONF_TEMPERATURE_ENTITY,
    DOMAIN,
    SUBENTRY_ROOM,
)
from .core.estimation import known_shares_exceed_total
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
from .core.room import (
    CEILING_M_MAX,
    CEILING_M_MIN,
    DEFAULT_CEILING_HEIGHT_M,
    DEFAULT_DESIGN_INDOOR_C,
    DEFAULT_EXTERIOR_WALLS,
    DESIGN_INDOOR_C_MAX,
    DESIGN_INDOOR_C_MIN,
    EXTERIOR_WALLS_MAX,
    EXTERIOR_WALLS_MIN,
    FLOOR_AREA_M2_MAX,
    FLOOR_AREA_M2_MIN,
    KNOWN_SHARE_PCT_MAX,
    KNOWN_SHARE_PCT_MIN,
    Above,
    Below,
    ShareMode,
    validate_design_indoor,
    validate_room,
)
from .house_config import house_from_config, house_from_entry, room_from_config, rooms_from_entry

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
        optional(CONF_LIVING_AREA): _number(
            LIVING_AREA_M2_MIN, LIVING_AREA_M2_MAX, 1, UnitOfArea.SQUARE_METERS
        ),
        optional(CONF_SHARE_OUTSIDE): _number(SHARE_PCT_MIN, SHARE_PCT_MAX, 1, PERCENTAGE),
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

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_ROOM: RoomSubentryFlow}


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


def _select(options: list[str], translation_key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options, translation_key=translation_key, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _suggested(defaults: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    value = defaults.get(key)
    return {"suggested_value": value} if value is not None else None


class RoomSubentryFlow(ConfigSubentryFlow):
    """Add or change a room (HAI-005). Step 1: basics; step 2: geometry or known share."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._basics("user", user_input, {})

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        return await self._basics("reconfigure", user_input, self._get_reconfigure_subentry().data)

    async def _basics(
        self, step_id: str, user_input: dict[str, Any] | None, defaults: Mapping[str, Any]
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not str(user_input.get(CONF_NAME, "")).strip():
                errors[CONF_NAME] = "name_empty"
            design_issue = validate_design_indoor(
                float(user_input.get(CONF_DESIGN_INDOOR, DEFAULT_DESIGN_INDOOR_C))
            )
            if design_issue is not None:
                errors[design_issue.field] = design_issue.code
            if not errors:
                self._data = {**defaults, **user_input}
                if user_input.get(CONF_AREA) is None:
                    self._data.pop(CONF_AREA, None)
                if ShareMode(user_input[CONF_SHARE_MODE]) is ShareMode.KNOWN:
                    return await self.async_step_known_share()
                return await self.async_step_geometry()
        values = user_input or defaults
        schema = {
            vol.Required(CONF_NAME, default=values.get(CONF_NAME, vol.UNDEFINED)): TextSelector(),
            vol.Optional(CONF_AREA, description=_suggested(values, CONF_AREA)): AreaSelector(),
            vol.Required(
                CONF_TEMPERATURE_ENTITY, default=values.get(CONF_TEMPERATURE_ENTITY, vol.UNDEFINED)
            ): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.TEMPERATURE)
            ),
            vol.Required(
                CONF_SHARE_MODE, default=values.get(CONF_SHARE_MODE, ShareMode.ESTIMATED.value)
            ): _select([m.value for m in ShareMode], CONF_SHARE_MODE),
            vol.Required(
                CONF_DESIGN_INDOOR,
                default=values.get(CONF_DESIGN_INDOOR, DEFAULT_DESIGN_INDOOR_C),
            ): _number(DESIGN_INDOOR_C_MIN, DESIGN_INDOOR_C_MAX, 0.5, UnitOfTemperature.CELSIUS),
        }
        return self.async_show_form(step_id=step_id, data_schema=vol.Schema(schema), errors=errors)

    async def async_step_geometry(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {**self._data, **user_input}
            if user_input.get(CONF_CEILING_LOW) is None:
                candidate.pop(CONF_CEILING_LOW, None)
            errors = _room_errors(candidate)
            if not errors:
                self._data = candidate
                return self._finish()
        values = user_input or self._data
        schema = {
            vol.Required(CONF_FLOOR_AREA, description=_suggested(values, CONF_FLOOR_AREA)): _number(
                FLOOR_AREA_M2_MIN, FLOOR_AREA_M2_MAX, 0.5, UnitOfArea.SQUARE_METERS
            ),
            vol.Required(
                CONF_CEILING_HEIGHT,
                default=values.get(CONF_CEILING_HEIGHT, DEFAULT_CEILING_HEIGHT_M),
            ): _number(CEILING_M_MIN, CEILING_M_MAX, 0.05, "m"),
            vol.Optional(
                CONF_CEILING_LOW, description=_suggested(values, CONF_CEILING_LOW)
            ): _number(CEILING_M_MIN, CEILING_M_MAX, 0.05, "m"),
            vol.Required(
                CONF_EXTERIOR_WALLS,
                default=values.get(CONF_EXTERIOR_WALLS, DEFAULT_EXTERIOR_WALLS),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=EXTERIOR_WALLS_MIN,
                    max=EXTERIOR_WALLS_MAX,
                    step=1,
                    mode=NumberSelectorMode.SLIDER,
                )
            ),
            vol.Required(CONF_ABOVE, default=values.get(CONF_ABOVE, Above.HEATED.value)): _select(
                [a.value for a in Above], CONF_ABOVE
            ),
            vol.Required(CONF_BELOW, default=values.get(CONF_BELOW, Below.HEATED.value)): _select(
                [b.value for b in Below], CONF_BELOW
            ),
        }
        return self.async_show_form(
            step_id="geometry", data_schema=vol.Schema(schema), errors=errors
        )

    async def async_step_known_share(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {**self._data, **user_input}
            errors = _room_errors(candidate)
            if not errors and self._known_shares_too_high(candidate):
                errors[CONF_KNOWN_SHARE] = "known_shares_exceed_total"
            if not errors:
                self._data = candidate
                return self._finish()
        values = user_input or self._data
        schema = {
            vol.Required(
                CONF_KNOWN_SHARE, description=_suggested(values, CONF_KNOWN_SHARE)
            ): _number(KNOWN_SHARE_PCT_MIN, KNOWN_SHARE_PCT_MAX, 0.1, PERCENTAGE),
        }
        return self.async_show_form(
            step_id="known_share", data_schema=vol.Schema(schema), errors=errors
        )

    def _known_shares_too_high(self, candidate: Mapping[str, Any]) -> bool:
        entry = self._get_entry()
        own_id = (
            self._get_reconfigure_subentry().subentry_id
            if self.source == SOURCE_RECONFIGURE
            else None
        )
        rooms = rooms_from_entry(entry, exclude=own_id) | {"new": room_from_config(candidate)}
        return known_shares_exceed_total(house_from_entry(entry), rooms)

    def _finish(self) -> SubentryFlowResult:
        title = str(self._data[CONF_NAME]).strip()
        if self.source == SOURCE_RECONFIGURE:
            return self.async_update_and_abort(
                self._get_entry(), self._get_reconfigure_subentry(), title=title, data=self._data
            )
        return self.async_create_entry(title=title, data=self._data)


def _room_errors(config: Mapping[str, Any]) -> dict[str, str]:
    return {issue.field: issue.code for issue in validate_room(room_from_config(config))}
