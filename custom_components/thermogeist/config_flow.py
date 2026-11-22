# SPDX-License-Identifier: MIT
"""Setup and options dialogs for a house, its rooms and thermostats (spec HAI-001 to HAI-006)."""

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
from homeassistant.data_entry_flow import section
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    AreaSelector,
    DeviceSelector,
    DeviceSelectorConfig,
    EntityFilterSelectorConfig,
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
from homeassistant.util.ulid import ulid_now

from .const import (
    CONF_ABOVE,
    CONF_AREA,
    CONF_BELOW,
    CONF_CEILING_HEIGHT,
    CONF_CEILING_LOW,
    CONF_DESIGN_INDOOR,
    CONF_DESIGN_TEMPERATURE,
    CONF_DEVICE,
    CONF_EXTERIOR_WALLS,
    CONF_FLOOR_AREA,
    CONF_FLOW_TEMPERATURE_ENTITY,
    CONF_HEAT_LOAD,
    CONF_HEAT_SOURCES,
    CONF_HEATING_TYPE,
    CONF_KNOWN_SHARE,
    CONF_LIVING_AREA,
    CONF_NAME,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_PROFILE,
    CONF_RATED_OUTPUT,
    CONF_RETURN_TEMPERATURE_ENTITY,
    CONF_ROLES,
    CONF_SHARE_MODE,
    CONF_SHARE_OUTSIDE,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_FACTOR,
    CONF_SOURCE_FACTOR_ENTITY,
    CONF_STRATEGY,
    CONF_TEMPERATURE_ENTITY,
    CONF_THERMOSTAT_NAME,
    CONF_THERMOSTATS,
    CONF_VALVE_MIN_INVERTED,
    CONF_VALVE_REFRESH,
    CONF_WINDOWS,
    DOMAIN,
    RATED_OUTPUT_W_MAX,
    RATED_OUTPUT_W_MIN,
    SUBENTRY_ROOM,
)
from .core.actuator import (
    DeviceEntity,
    DeviceProfile,
    EntityFacts,
    Role,
    Source,
    Strategy,
    check_role,
    find_profile,
    resolve_roles,
)
from .core.estimation import known_shares_exceed_total
from .core.exposes import profile_from_exposes
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
    HEAT_SOURCE_FACTOR_DEFAULT_PCT,
    HEAT_SOURCE_FACTOR_MAX_PCT,
    HEAT_SOURCE_FACTOR_MIN_PCT,
    KNOWN_SHARE_PCT_MAX,
    KNOWN_SHARE_PCT_MIN,
    Above,
    Below,
    ShareMode,
    validate_design_indoor,
    validate_room,
)
from .device_profiles import async_get_profiles
from .house_config import house_from_config, house_from_entry, room_from_config, rooms_from_entry
from .z2m import device_definition

CONF_THERMOSTAT = "thermostat"
AUTO_PROFILE_NAME = {
    "en": "Detected from Zigbee2MQTT (not tested)",
    "de": "Aus Zigbee2MQTT erkannt (nicht getestet)",
}
"""ACT-038: shown instead of a profile name for automatically detected thermostats."""
"""Field of the pick step (edit or remove a thermostat)."""

SECTION_WINDOWS_DEVICES = "windows_devices"
SECTION_MORE = "more"
SECTION_SLOPED_CEILING = "sloped_ceiling"
SECTION_FACTOR_SENSORS = "factor_sensors"
SECTION_DETECTED_ROLES = "detected_roles"
SECTIONS = (
    SECTION_WINDOWS_DEVICES,
    SECTION_MORE,
    SECTION_SLOPED_CEILING,
    SECTION_FACTOR_SENSORS,
    SECTION_DETECTED_ROLES,
)
"""HAI-016: collapsible sections; their fields are stored flat."""


def _flatten(user_input: Mapping[str, Any]) -> dict[str, Any]:
    """Merge the fields of collapsible sections into the top level."""
    flat: dict[str, Any] = {}
    for key, value in user_input.items():
        if key in SECTIONS and isinstance(value, Mapping):
            flat.update(value)
        else:
            flat[key] = value
    return flat


def _section(fields: Mapping[vol.Marker, Any], *, open_: bool) -> section:
    """HAI-016: collapsed unless it already holds a value."""
    return section(vol.Schema(dict(fields)), {"collapsed": not open_})


HEAT_LOAD_KNOWN = "heat_load_known"
"""HAI-018: question whether a heat load calculation exists."""
FLOW_MEASUREMENT = "flow_measurement"
"""HAI-018: question which water temperatures are measured."""
YES, NO = "yes", "no"
FLOW_NONE, FLOW_ONLY, FLOW_AND_RETURN = "none", "flow", "flow_return"
HEAT_LOAD_KEYS = (CONF_HEAT_LOAD, CONF_DESIGN_TEMPERATURE, CONF_SHARE_OUTSIDE)
FLOW_KEYS = (CONF_FLOW_TEMPERATURE_ENTITY, CONF_RETURN_TEMPERATURE_ENTITY)
HOUSE_OPTION_KEYS = (
    CONF_HEATING_TYPE,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_LIVING_AREA,
    *HEAT_LOAD_KEYS,
    *FLOW_KEYS,
)


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


def _optional(defaults: Mapping[str, Any], key: str) -> vol.Optional:
    value = defaults.get(key)
    return vol.Optional(key, description={"suggested_value": value} if value is not None else None)


def _temperature_sensor() -> EntitySelector:
    return EntitySelector(
        EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.TEMPERATURE)
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
        ): _temperature_sensor(),
    }


def _flow_answer(defaults: Mapping[str, Any]) -> str:
    if defaults.get(CONF_RETURN_TEMPERATURE_ENTITY):
        return FLOW_AND_RETURN
    return FLOW_ONLY if defaults.get(CONF_FLOW_TEMPERATURE_ENTITY) else FLOW_NONE


def _question_schema(defaults: Mapping[str, Any]) -> dict[vol.Marker, Any]:
    """HAI-018: the answers decide the next steps; pre-selected from current values."""
    return {
        vol.Required(
            HEAT_LOAD_KNOWN,
            default=defaults.get(HEAT_LOAD_KNOWN, YES if defaults.get(CONF_HEAT_LOAD) else NO),
        ): SelectSelector(
            SelectSelectorConfig(
                options=[YES, NO], translation_key=HEAT_LOAD_KNOWN, mode=SelectSelectorMode.LIST
            )
        ),
        vol.Required(
            FLOW_MEASUREMENT, default=defaults.get(FLOW_MEASUREMENT, _flow_answer(defaults))
        ): SelectSelector(
            SelectSelectorConfig(
                options=[FLOW_NONE, FLOW_ONLY, FLOW_AND_RETURN],
                translation_key=FLOW_MEASUREMENT,
                mode=SelectSelectorMode.LIST,
            )
        ),
        _optional(defaults, CONF_LIVING_AREA): _number(
            LIVING_AREA_M2_MIN, LIVING_AREA_M2_MAX, 1, UnitOfArea.SQUARE_METERS
        ),
    }


def _heat_load_schema(defaults: Mapping[str, Any]) -> dict[vol.Marker, Any]:
    return {
        _optional(defaults, CONF_HEAT_LOAD): _number(
            HEAT_LOAD_KW_MIN, HEAT_LOAD_KW_MAX, 0.1, UnitOfPower.KILO_WATT
        ),
        _optional(defaults, CONF_DESIGN_TEMPERATURE): _number(
            DESIGN_TEMP_C_MIN, DESIGN_TEMP_C_MAX, 0.5, UnitOfTemperature.CELSIUS
        ),
        _optional(defaults, CONF_SHARE_OUTSIDE): _number(
            SHARE_PCT_MIN, SHARE_PCT_MAX, 1, PERCENTAGE
        ),
    }


def _flow_schema(defaults: Mapping[str, Any], *, with_return: bool) -> dict[vol.Marker, Any]:
    schema: dict[vol.Marker, Any] = {
        vol.Required(
            CONF_FLOW_TEMPERATURE_ENTITY,
            default=defaults.get(CONF_FLOW_TEMPERATURE_ENTITY, vol.UNDEFINED),
        ): _temperature_sensor()
    }
    if with_return:
        schema[
            vol.Required(
                CONF_RETURN_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_RETURN_TEMPERATURE_ENTITY, vol.UNDEFINED),
            )
        ] = _temperature_sensor()
    return schema


def _errors(config: Mapping[str, Any]) -> dict[str, str]:
    """Validate with the core and map issues to form fields."""
    return {issue.field: issue.code for issue in validate_house(house_from_config(config))}


class HouseQuestions:
    """HAI-018: steps after the questions, shared by setup and options."""

    _data: dict[str, Any]
    async_show_form: Any
    """Provided by the config and options flow classes."""

    async def _finish_house(self) -> Any:
        raise NotImplementedError

    def _answers(self, user_input: Mapping[str, Any]) -> None:
        """Keep the answers; inputs that belong to a *no* are cleared."""
        self._data.update(user_input)
        if user_input.get(CONF_LIVING_AREA) is None:
            self._data.pop(CONF_LIVING_AREA, None)
        if user_input[HEAT_LOAD_KNOWN] == NO:
            for key in HEAT_LOAD_KEYS:
                self._data.pop(key, None)
        if user_input[FLOW_MEASUREMENT] == FLOW_NONE:
            for key in FLOW_KEYS:
                self._data.pop(key, None)
        elif user_input[FLOW_MEASUREMENT] == FLOW_ONLY:
            self._data.pop(CONF_RETURN_TEMPERATURE_ENTITY, None)

    async def _next_after_questions(self) -> Any:
        if self._data[HEAT_LOAD_KNOWN] == YES:
            return await self.async_step_heat_load()
        return await self._next_after_heat_load()

    async def _next_after_heat_load(self) -> Any:
        if self._data[FLOW_MEASUREMENT] != FLOW_NONE:
            return await self.async_step_flow()
        return await self._finish_house()

    async def async_step_heat_load(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            candidate = {**self._data, **user_input}
            for key in HEAT_LOAD_KEYS:
                if user_input.get(key) is None:
                    candidate.pop(key, None)
            errors = _errors(candidate)
            if not errors:
                self._data = candidate
                return await self._next_after_heat_load()
        return self.async_show_form(
            step_id="heat_load",
            data_schema=vol.Schema(_heat_load_schema(user_input or self._data)),
            errors=errors,
            last_step=self._data[FLOW_MEASUREMENT] == FLOW_NONE,
        )

    async def async_step_flow(self, user_input: dict[str, Any] | None = None) -> Any:
        with_return = self._data[FLOW_MEASUREMENT] == FLOW_AND_RETURN
        if user_input is not None:
            self._data.update(user_input)
            return await self._finish_house()
        return self.async_show_form(
            step_id="flow",
            data_schema=vol.Schema(_flow_schema(self._data, with_return=with_return)),
            last_step=True,
        )


def _house_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Stored house data without the dialog's questions."""
    return {k: v for k, v in data.items() if k not in (HEAT_LOAD_KNOWN, FLOW_MEASUREMENT)}


class ThermogeistConfigFlow(HouseQuestions, ConfigFlow, domain=DOMAIN):
    """Required answers, then questions that decide which details are asked (HAI-018)."""

    VERSION = 1
    MINOR_VERSION = 2

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
            last_step=False,
            data_schema=vol.Schema(_required_schema(user_input or {})),
            errors=errors,
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._answers(user_input)
            return await self._next_after_questions()
        return self.async_show_form(
            step_id="details",
            last_step=False,
            data_schema=vol.Schema(_question_schema(self._data)),
        )

    async def _finish_house(self) -> ConfigFlowResult:
        data = _house_data(self._data)
        return self.async_create_entry(title=data[CONF_NAME].strip(), data=data)

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


class ThermogeistOptionsFlow(HouseQuestions, OptionsFlow):
    """Change every house setting later (HAI-003). The name stays the entry title."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _errors({CONF_NAME: current[CONF_NAME], **current, **user_input})
            if not errors:
                self._data = {
                    k: v for k, v in current.items() if k in (CONF_NAME, *HOUSE_OPTION_KEYS)
                }
                self._answers(user_input)
                return await self._next_after_questions()
        defaults = user_input or current
        return self.async_show_form(
            step_id="init",
            last_step=False,
            data_schema=vol.Schema(
                _required_schema(defaults, include_name=False) | _question_schema(defaults)
            ),
            errors=errors,
        )

    async def _finish_house(self) -> ConfigFlowResult:
        # Every key is written so a cleared input overrides an older value in the entry data.
        return self.async_create_entry(data={key: self._data.get(key) for key in HOUSE_OPTION_KEYS})


def _select(options: list[str], translation_key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options, translation_key=translation_key, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _suggested(defaults: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    value = defaults.get(key)
    return {"suggested_value": value} if value is not None else None


class ThermostatSteps(ConfigSubentryFlow):
    """Thermostat steps inside the room dialog (HAI-006, HAI-007): device, then roles."""

    def _init_thermostat(self) -> None:
        self._tdata: dict[str, Any] = {}
        self._thermostat_defaults: dict[str, Any] = {}
        self._thermostat_id: str | None = None
        self._detected: dict[str, str] = {}
        self._profile_name: str | None = None
        self._refresh: float | None = None
        self._strategy: str = Strategy.AUTOMATIC
        self._notes: str = ""

    async def _save_thermostat(self, thermostat: dict[str, Any]) -> SubentryFlowResult:
        raise NotImplementedError

    async def async_step_thermostat(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Device and radiator of a thermostat in this room (HAI-007)."""
        defaults = self._thermostat_defaults
        if user_input is not None:
            self._tdata = {**defaults, **user_input}
            if user_input.get(CONF_RATED_OUTPUT) is None:
                self._tdata.pop(CONF_RATED_OUTPUT, None)
            await self._detect(user_input[CONF_DEVICE], defaults)
            return await self.async_step_roles()
        schema = {
            vol.Required(
                CONF_DEVICE, default=defaults.get(CONF_DEVICE, vol.UNDEFINED)
            ): DeviceSelector(
                DeviceSelectorConfig(entity=[EntityFilterSelectorConfig(domain="climate")])
            ),
            vol.Optional(
                CONF_RATED_OUTPUT, description=_suggested(defaults, CONF_RATED_OUTPUT)
            ): _number(RATED_OUTPUT_W_MIN, RATED_OUTPUT_W_MAX, 10, "W"),
        }
        return self.async_show_form(
            step_id="thermostat", data_schema=vol.Schema(schema), last_step=False
        )

    def _profile_from_z2m(self, device: dr.DeviceEntry) -> DeviceProfile | None:
        """ACT-034, ACT-038: roles from the device's Zigbee2MQTT exposes, marked untested."""
        definition = device_definition(self.hass, device)
        if not definition:
            return None
        name = AUTO_PROFILE_NAME.get(self.hass.config.language, AUTO_PROFILE_NAME["en"])
        return profile_from_exposes(definition.get("exposes") or (), name)

    async def _detect(self, device_id: str, defaults: Mapping[str, Any]) -> None:
        """Find profile and roles for the device (ACT-031, ACT-032)."""
        device = dr.async_get(self.hass).async_get(device_id)
        entries = er.async_entries_for_device(er.async_get(self.hass), device_id)
        profiles = await async_get_profiles(self.hass)
        profile = find_profile(profiles, device.manufacturer, device.model_id) if device else None
        if profile is None and device is not None:
            profile = self._profile_from_z2m(device)
        detected = resolve_roles(
            [DeviceEntity(e.entity_id, e.unique_id, e.domain) for e in entries], profile
        )
        same_device = defaults.get(CONF_DEVICE) == device_id and defaults.get(CONF_ROLES)
        self._detected = (
            dict(defaults[CONF_ROLES]) if same_device else {r.value: e for r, e in detected.items()}
        )
        self._profile_name = profile.name if profile else None
        self._notes = " ".join(profile.notes) if profile else ""
        self._tdata[CONF_PROFILE] = profile.profile_id if profile else None
        inverted = False
        if profile and Role.VALVE_MIN in profile.roles.get(Source.Z2M, {}):
            inverted = profile.roles[Source.Z2M][Role.VALVE_MIN].inverted
        self._tdata[CONF_VALVE_MIN_INVERTED] = inverted
        if same_device and CONF_VALVE_REFRESH in defaults:
            self._refresh = defaults.get(CONF_VALVE_REFRESH)
        else:
            self._refresh = (
                profile.valve_refresh.total_seconds() / 60
                if profile and profile.valve_refresh
                else None
            )
        self._strategy = str(
            defaults.get(CONF_STRATEGY, Strategy.AUTOMATIC) if same_device else Strategy.AUTOMATIC
        )
        self._tdata["_device_name"] = (device.name_by_user or device.name) if device else device_id

    async def async_step_roles(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _flatten(user_input)
            self._refresh = user_input.pop(CONF_VALVE_REFRESH, None)
            self._strategy = user_input.pop(CONF_STRATEGY, Strategy.AUTOMATIC)
            roles = {role: entity for role, entity in user_input.items() if entity}
            if Role.CLIMATE.value not in roles:
                errors[Role.CLIMATE.value] = "climate_required"
            if self._strategy == Strategy.VALVE and Role.VALVE_WRITE.value not in roles:
                errors[CONF_STRATEGY] = "valve_strategy_needs_valve_write"
            errors |= self._implausible_roles(roles)
            if not errors:
                return await self._finish_thermostat(roles)
        roles: dict[vol.Marker, Any] = {}
        more: dict[vol.Marker, Any] = {}
        for role, domains in ROLE_DOMAINS.items():
            marker = vol.Required if role is Role.CLIMATE else vol.Optional
            # Any entity of a fitting domain may be chosen: some integrations (e.g. Bosch SHC)
            # put the climate entity on a different device than the valve sensor (ACT-033).
            target = more if role in ADVANCED_ROLES else roles
            target[marker(role.value, description=_suggested(self._detected, role.value))] = (
                EntitySelector(EntitySelectorConfig(domain=domains))
            )
        more[
            vol.Optional(
                CONF_VALVE_REFRESH,
                description={"suggested_value": self._refresh} if self._refresh else None,
            )
        ] = _number(1, 60, 1, "min")
        schema: dict[vol.Marker, Any] = {
            vol.Required(CONF_STRATEGY, default=self._strategy): _select(
                [s.value for s in Strategy], "strategy"
            )
        }
        detected = self._profile_name is not None and len(self._detected) > 1
        if detected:
            # HAI-020: found by a profile or Zigbee2MQTT - checking them is optional.
            schema[vol.Required(SECTION_DETECTED_ROLES)] = _section(roles, open_=bool(errors))
        else:
            schema |= roles
        schema[vol.Required(SECTION_MORE)] = _section(
            more,
            open_=bool(errors) or any(self._detected.get(r.value) for r in ADVANCED_ROLES),
        )
        return self.async_show_form(
            step_id="roles",
            last_step=True,
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "profile": self._profile_name or "-",
                "notes": self._notes,
            },
        )

    def _implausible_roles(self, roles: dict[str, str]) -> dict[str, str]:
        """ACT-035: e.g. a temperature sensor chosen as valve position is rejected."""
        errors: dict[str, str] = {}
        for role_key, entity_id in roles.items():
            state = self.hass.states.get(entity_id)
            attributes = state.attributes if state else {}
            facts = EntityFacts(
                state=state.state if state else None,
                unit=attributes.get("unit_of_measurement"),
                device_class=attributes.get("device_class"),
                options=tuple(attributes.get("options") or ()),
            )
            if (code := check_role(Role(role_key), facts)) is not None:
                errors[role_key] = code
        read = roles.get(Role.VALVE_READ.value)
        profile_read = self._detected.get(Role.VALVE_READ.value)
        if read is not None and read == roles.get(Role.VALVE_WRITE.value) and read != profile_read:
            # ACT-036: the written value only echoes Thermogeist, it is no position - unless the
            # profile knows the device keeps regulating it itself (Bosch pi_heating_demand).
            errors[Role.VALVE_READ.value] = "valve_read_is_write"
        return errors

    async def _finish_thermostat(self, roles: dict[str, str]) -> SubentryFlowResult:
        data = {
            CONF_THERMOSTAT_NAME: str(self._tdata.pop("_device_name")),
            CONF_DEVICE: self._tdata[CONF_DEVICE],
            CONF_PROFILE: self._tdata.get(CONF_PROFILE),
            CONF_VALVE_MIN_INVERTED: self._tdata.get(CONF_VALVE_MIN_INVERTED, False),
            CONF_ROLES: roles,
            CONF_VALVE_REFRESH: self._refresh or None,
            CONF_STRATEGY: self._strategy,
        }
        if self._tdata.get(CONF_RATED_OUTPUT) is not None:
            data[CONF_RATED_OUTPUT] = self._tdata[CONF_RATED_OUTPUT]
        return await self._save_thermostat(data)


class RoomSubentryFlow(ThermostatSteps):
    """Add or change a room (HAI-005).

    Step 1: basics; step 2: geometry or known share; step 3 only with heat sources: factors.
    The gear icon opens a menu: edit the room, add, edit or remove its thermostats (HAI-007).
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._source_ids: list[str] = []
        self._factors: dict[str, float] = {}
        self._factor_entities: dict[str, str] = {}
        self._init_thermostat()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._basics("user", user_input, {})

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        options = ["edit_room", "add_thermostat"]
        if self._room_thermostats():
            options += ["edit_thermostat", "remove_thermostat"]
        return self.async_show_menu(step_id="reconfigure", menu_options=options)

    async def async_step_edit_room(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        return await self._basics("edit_room", user_input, self._get_reconfigure_subentry().data)

    async def async_step_add_thermostat(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        self._thermostat_id = ulid_now()
        self._thermostat_defaults = {}
        return await self.async_step_thermostat()

    async def async_step_edit_thermostat(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        if user_input is not None:
            self._thermostat_id = user_input[CONF_THERMOSTAT]
            self._thermostat_defaults = dict(self._room_thermostats()[self._thermostat_id])
            return await self.async_step_thermostat()
        return self.async_show_form(
            step_id="edit_thermostat", data_schema=self._pick_schema(), last_step=False
        )

    async def async_step_remove_thermostat(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """The device gets its settings back on the next start (ACT-008)."""
        if user_input is not None:
            thermostats = self._room_thermostats()
            thermostats.pop(user_input[CONF_THERMOSTAT], None)
            return self._update_room({CONF_THERMOSTATS: thermostats})
        return self.async_show_form(
            step_id="remove_thermostat", data_schema=self._pick_schema(), last_step=True
        )

    def _pick_schema(self) -> vol.Schema:
        options = [
            {"value": tid, "label": str(data.get(CONF_THERMOSTAT_NAME, tid))}
            for tid, data in self._room_thermostats().items()
        ]
        return vol.Schema(
            {
                vol.Required(CONF_THERMOSTAT): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                )
            }
        )

    def _room_thermostats(self) -> dict[str, dict[str, Any]]:
        stored = self._get_reconfigure_subentry().data.get(CONF_THERMOSTATS) or {}
        return {tid: dict(data) for tid, data in stored.items()}

    async def _save_thermostat(self, thermostat: dict[str, Any]) -> SubentryFlowResult:
        assert self._thermostat_id is not None
        if self.source != SOURCE_RECONFIGURE:
            # HAI-021: a new room collects its thermostats and is saved at "Done".
            self._data.setdefault(CONF_THERMOSTATS, {})[self._thermostat_id] = thermostat
            return await self.async_step_new_room_thermostats()
        thermostats = self._room_thermostats()
        thermostats[self._thermostat_id] = thermostat
        return self._update_room({CONF_THERMOSTATS: thermostats})

    async def async_step_new_room_thermostats(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """HAI-021: add a thermostat right away, or save the room."""
        return self.async_show_menu(
            step_id="new_room_thermostats",
            menu_options=["add_new_room_thermostat", "new_room_done"],
            description_placeholders={
                "room": str(self._data.get(CONF_NAME, "")).strip(),
                "count": str(len(self._data.get(CONF_THERMOSTATS) or {})),
            },
        )

    async def async_step_add_new_room_thermostat(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        self._thermostat_id = ulid_now()
        self._thermostat_defaults = {}
        return await self.async_step_thermostat()

    async def async_step_new_room_done(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        return self.async_create_entry(title=str(self._data[CONF_NAME]).strip(), data=self._data)

    def _update_room(self, changes: Mapping[str, Any]) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        return self.async_update_and_abort(
            self._get_entry(), subentry, data={**subentry.data, **changes}
        )

    async def _basics(
        self, step_id: str, user_input: dict[str, Any] | None, defaults: Mapping[str, Any]
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _flatten(user_input)
            if not str(user_input.get(CONF_NAME, "")).strip():
                errors[CONF_NAME] = "name_empty"
            design_issue = validate_design_indoor(
                float(user_input.get(CONF_DESIGN_INDOOR, DEFAULT_DESIGN_INDOOR_C))
            )
            if design_issue is not None:
                errors[design_issue.field] = design_issue.code
            if not errors:
                user_input = dict(user_input)
                self._source_ids = list(user_input.pop(CONF_HEAT_SOURCES, None) or [])
                self._factors = {
                    s[CONF_SOURCE_ENTITY]: s[CONF_SOURCE_FACTOR]
                    for s in defaults.get(CONF_HEAT_SOURCES) or ()
                }
                self._factor_entities = {
                    s[CONF_SOURCE_ENTITY]: s[CONF_SOURCE_FACTOR_ENTITY]
                    for s in defaults.get(CONF_HEAT_SOURCES) or ()
                    if s.get(CONF_SOURCE_FACTOR_ENTITY)
                }
                self._data = {**defaults, **user_input}
                self._data.pop(CONF_HEAT_SOURCES, None)
                if user_input.get(CONF_AREA) is None:
                    self._data.pop(CONF_AREA, None)
                if not user_input.get(CONF_WINDOWS):
                    self._data.pop(CONF_WINDOWS, None)
                if ShareMode(user_input[CONF_SHARE_MODE]) is ShareMode.KNOWN:
                    return await self.async_step_known_share()
                return await self.async_step_geometry()
        values = dict(user_input or defaults)
        if values.get(CONF_HEAT_SOURCES) and isinstance(values[CONF_HEAT_SOURCES][0], dict):
            values[CONF_HEAT_SOURCES] = [s[CONF_SOURCE_ENTITY] for s in values[CONF_HEAT_SOURCES]]
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
            vol.Required(SECTION_WINDOWS_DEVICES): _section(
                {
                    vol.Optional(
                        CONF_WINDOWS, description=_suggested(values, CONF_WINDOWS)
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain="binary_sensor",
                            device_class=["window", "door", "opening"],
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_HEAT_SOURCES, description=_suggested(values, CONF_HEAT_SOURCES)
                    ): EntitySelector(
                        EntitySelectorConfig(
                            domain="sensor", device_class=SensorDeviceClass.POWER, multiple=True
                        )
                    ),
                },
                open_=bool(values.get(CONF_WINDOWS) or values.get(CONF_HEAT_SOURCES)),
            ),
            vol.Required(SECTION_MORE): _section(
                {
                    vol.Required(
                        CONF_DESIGN_INDOOR,
                        default=values.get(CONF_DESIGN_INDOOR, DEFAULT_DESIGN_INDOOR_C),
                    ): _number(
                        DESIGN_INDOOR_C_MIN, DESIGN_INDOOR_C_MAX, 0.5, UnitOfTemperature.CELSIUS
                    ),
                },
                open_=values.get(CONF_DESIGN_INDOOR, DEFAULT_DESIGN_INDOOR_C)
                != DEFAULT_DESIGN_INDOOR_C,
            ),
        }
        return self.async_show_form(
            step_id=step_id, data_schema=vol.Schema(schema), errors=errors, last_step=False
        )

    async def async_step_geometry(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _flatten(user_input)
            candidate = {**self._data, **user_input}
            if user_input.get(CONF_CEILING_LOW) is None:
                candidate.pop(CONF_CEILING_LOW, None)
            errors = _room_errors(candidate)
            if not errors:
                self._data = candidate
                return await self._after_share()
        values = user_input or self._data
        schema = {
            vol.Required(CONF_FLOOR_AREA, description=_suggested(values, CONF_FLOOR_AREA)): _number(
                FLOOR_AREA_M2_MIN, FLOOR_AREA_M2_MAX, 0.5, UnitOfArea.SQUARE_METERS
            ),
            vol.Required(
                CONF_CEILING_HEIGHT,
                default=values.get(CONF_CEILING_HEIGHT, DEFAULT_CEILING_HEIGHT_M),
            ): _number(CEILING_M_MIN, CEILING_M_MAX, 0.05, "m"),
            vol.Required(SECTION_SLOPED_CEILING): _section(
                {
                    vol.Optional(
                        CONF_CEILING_LOW, description=_suggested(values, CONF_CEILING_LOW)
                    ): _number(CEILING_M_MIN, CEILING_M_MAX, 0.05, "m"),
                },
                open_=values.get(CONF_CEILING_LOW) is not None,
            ),
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
            step_id="geometry",
            data_schema=vol.Schema(schema),
            errors=errors,
            last_step=self._last_room_step(),
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
                return await self._after_share()
        values = user_input or self._data
        schema = {
            vol.Required(
                CONF_KNOWN_SHARE, description=_suggested(values, CONF_KNOWN_SHARE)
            ): _number(KNOWN_SHARE_PCT_MIN, KNOWN_SHARE_PCT_MAX, 0.1, PERCENTAGE),
        }
        return self.async_show_form(
            step_id="known_share",
            data_schema=vol.Schema(schema),
            errors=errors,
            last_step=self._last_room_step(),
        )

    def _last_room_step(self) -> bool:
        """New rooms continue with the thermostat question (HAI-021)."""
        return self.source == SOURCE_RECONFIGURE and not self._source_ids

    async def _after_share(self) -> SubentryFlowResult:
        if self._source_ids:
            return await self.async_step_heat_source_factors()
        return await self._finish()

    async def async_step_heat_source_factors(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """MDL-042, MDL-049: how much of each device's power stays in the room."""
        if user_input is not None:
            user_input = _flatten(user_input)
            self._data[CONF_HEAT_SOURCES] = [
                _heat_source(entity_id, user_input) for entity_id in self._source_ids
            ]
            return await self._finish()
        schema: dict[Any, Any] = {}
        sensors: dict[Any, Any] = {}
        for entity_id in self._source_ids:
            schema[
                vol.Required(
                    entity_id,
                    default=self._factors.get(entity_id, HEAT_SOURCE_FACTOR_DEFAULT_PCT),
                )
            ] = _number(HEAT_SOURCE_FACTOR_MIN_PCT, HEAT_SOURCE_FACTOR_MAX_PCT, 5, PERCENTAGE)
            factor_key = factor_entity_key(entity_id)
            sensors[
                vol.Optional(
                    factor_key,
                    description=_suggested(
                        {factor_key: self._factor_entities.get(entity_id)}, factor_key
                    ),
                )
            ] = EntitySelector(EntitySelectorConfig(domain=["sensor", "input_number", "number"]))
        schema[vol.Required(SECTION_FACTOR_SENSORS)] = _section(
            sensors, open_=any(self._factor_entities.get(e) for e in self._source_ids)
        )
        names = ", ".join(self._source_name(e) for e in self._source_ids)
        return self.async_show_form(
            step_id="heat_source_factors",
            data_schema=vol.Schema(schema),
            last_step=self.source == SOURCE_RECONFIGURE,
            description_placeholders={"devices": names},
        )

    def _source_name(self, entity_id: str) -> str:
        state = self.hass.states.get(entity_id)
        return str(state.name) if state else entity_id

    def _known_shares_too_high(self, candidate: Mapping[str, Any]) -> bool:
        entry = self._get_entry()
        own_id = (
            self._get_reconfigure_subentry().subentry_id
            if self.source == SOURCE_RECONFIGURE
            else None
        )
        rooms = rooms_from_entry(entry, exclude=own_id) | {"new": room_from_config(candidate)}
        return known_shares_exceed_total(house_from_entry(entry), rooms)

    async def _finish(self) -> SubentryFlowResult:
        title = str(self._data[CONF_NAME]).strip()
        if self.source == SOURCE_RECONFIGURE:
            return self.async_update_and_abort(
                self._get_entry(), self._get_reconfigure_subentry(), title=title, data=self._data
            )
        return await self.async_step_new_room_thermostats()


def _room_errors(config: Mapping[str, Any]) -> dict[str, str]:
    return {issue.field: issue.code for issue in validate_room(room_from_config(config))}


ADVANCED_ROLES = (Role.CALIBRATION_TRIGGER, Role.CALIBRATION_STATUS)
"""HAI-020: rarely changed; in the collapsed section *More*."""

# Which entity domains may fill a role (ACT-001 to ACT-009).
ROLE_DOMAINS: dict[Role, list[str]] = {
    Role.CLIMATE: ["climate"],
    Role.VALVE_READ: ["number", "sensor"],
    Role.VALVE_WRITE: ["number"],
    Role.VALVE_MIN: ["number"],
    Role.EXTERNAL_TEMPERATURE: ["number"],
    Role.CHILD_LOCK: ["switch", "lock", "select"],
    Role.CALIBRATION_TRIGGER: ["button", "select", "switch"],
    Role.CALIBRATION_STATUS: ["sensor", "select"],
}


def factor_entity_key(entity_id: str) -> str:
    """MDL-049: form field for the optional factor sensor of one heat source."""
    return f"{entity_id} (factor sensor)"


def _heat_source(entity_id: str, user_input: Mapping[str, Any]) -> dict[str, Any]:
    source: dict[str, Any] = {
        CONF_SOURCE_ENTITY: entity_id,
        CONF_SOURCE_FACTOR: float(user_input.get(entity_id, HEAT_SOURCE_FACTOR_DEFAULT_PCT)),
    }
    if factor_entity := user_input.get(factor_entity_key(entity_id)):
        source[CONF_SOURCE_FACTOR_ENTITY] = factor_entity
    return source
