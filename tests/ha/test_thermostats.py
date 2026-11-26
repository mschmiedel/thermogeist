# SPDX-License-Identifier: MIT
import json
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.core import HomeAssistant, State
from homeassistant.data_entry_flow import FlowResultType, section
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
    async_fire_time_changed,
    mock_restore_cache,
)

from .conftest import (
    HOUSE_WITH_LOAD,
    LIVING_ROOM,
    ROOM_SENSOR,
    report_room_temperature,
    setup_house,
)

FLOW_SENSOR = "sensor.flow_temperature"
RETURN_SENSOR = "sensor.return_temperature"
PLANNED = "sensor.living_room_planned_valve_position"


def z2m_device(
    hass: HomeAssistant, name: str, manufacturer: str, model_id: str, exposes: dict[str, Any]
) -> str:
    """Register a device the way Zigbee2MQTT does: unique ids '<ieee>_<expose>_zigbee2mqtt'."""
    mqtt = MockConfigEntry(domain="mqtt")
    mqtt.add_to_hass(hass)
    ieee = f"0x{abs(hash(name)) % 16**16:016x}"
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=mqtt.entry_id,
        identifiers={("mqtt", f"zigbee2mqtt_{ieee}")},
        manufacturer=manufacturer,
        model_id=model_id,
        name=name,
    )
    registry = er.async_get(hass)
    for expose, (domain, state, *unit) in exposes.items():
        entity = registry.async_get_or_create(
            domain,
            "mqtt",
            f"{ieee}_{expose}_zigbee2mqtt",
            device_id=device.id,
            config_entry=mqtt,
            suggested_object_id=f"{name.lower().replace(' ', '_')}_{expose}",
        )
        attributes = {"unit_of_measurement": unit[0]} if unit else {}
        hass.states.async_set(entity.entity_id, state, attributes)
    return device.id


def sonoff(hass: HomeAssistant) -> str:
    return z2m_device(
        hass,
        "Living TRV",
        "SONOFF",
        "TRVZB",
        {
            "climate": ("climate", "heat"),
            "valve_opening_degree": ("number", "100", "%"),
            "valve_closing_degree": ("number", "100", "%"),
            "external_temperature_input": ("number", "20", "°C"),
            "child_lock": ("switch", "off"),
        },
    )


def suggested(result: dict[str, Any]) -> dict[str, str]:
    """Pre-filled values of a form, also inside collapsible sections (HAI-016)."""
    values = {}
    for marker, value in result["data_schema"].schema.items():
        markers = value.schema.schema if isinstance(value, section) else {marker: value}
        for inner in markers:
            description = inner.description or {}
            if description.get("suggested_value"):
                values[str(inner)] = description["suggested_value"]
    return values


async def start_thermostat(
    hass: HomeAssistant,
    entry_id: str,
    room_id: str,
    device_id: str,
    rated: float | None = None,
) -> dict[str, Any]:
    """Room gear icon → Add thermostat → device step (HAI-007); returns the roles form."""
    result = await hass.config_entries.subentries.async_init(
        (entry_id, "room"), context={"source": SOURCE_RECONFIGURE, "subentry_id": room_id}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "add_thermostat"}
    )
    answers: dict[str, Any] = {"device": device_id}
    if rated is not None:
        answers["rated_output"] = rated
    return await hass.config_entries.subentries.async_configure(result["flow_id"], answers)


def thermostat_ids(entry: MockConfigEntry) -> list[str]:
    return [
        tid
        for s in entry.subentries.values()
        if s.subentry_type == "room"
        for tid in s.data.get("thermostats", {})
    ]


async def assign(
    hass: HomeAssistant,
    entry_id: str,
    room_id: str,
    device_id: str,
    rated: float | None,
    strategy: str | None = None,
) -> dict[str, Any]:
    result = await start_thermostat(hass, entry_id, room_id, device_id, rated)
    assert result["step_id"] == "roles"
    roles_form = result
    answers = suggested(result)
    if strategy is not None:
        answers["strategy"] = strategy
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], answers)
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    return roles_form


async def house_with_room(hass: HomeAssistant) -> tuple[MockConfigEntry, str]:
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [LIVING_ROOM]
    )
    return entry, next(iter(entry.subentries))


async def test_sonoff_is_recognised_and_planned(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-001"""
    entry, room_id = await house_with_room(hass)
    device_id = sonoff(hass)

    roles_form = await assign(hass, entry.entry_id, room_id, device_id, 2000.0)

    assert roles_form["description_placeholders"]["profile"] == "Sonoff TRVZB"
    roles = suggested(roles_form)
    assert roles["climate"] == "climate.living_trv_climate"
    assert roles["valve_write"] == "number.living_trv_valve_opening_degree"
    assert roles["valve_min"] == "number.living_trv_valve_closing_degree"

    planned = hass.states.get(PLANNED)
    assert planned.attributes["mode"] == "observe"
    assert planned.attributes["strategies"] == ["valve"]
    # CTL-030: the output is computed at the 20 °C target, not at the 19.5 °C room.
    assert planned.attributes["feed_forward"] == pytest.approx(64.5, abs=0.5)
    assert planned.attributes["feed_forward_missing"] == []
    assert float(planned.state) == pytest.approx(72, abs=1)
    assert hass.states.get("sensor.living_room_kind_living_trv").state == "valve"


async def test_bosch_shows_actual_next_to_planned(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-002"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(
        hass,
        "Bath TRV",
        "Bosch",
        "BTH-RA",
        {"climate": ("climate", "heat"), "pi_heating_demand": ("number", "39", "%")},
    )

    roles_form = await assign(hass, entry.entry_id, room_id, device_id, None)

    assert roles_form["description_placeholders"]["profile"].startswith("Bosch")
    actual = "sensor.living_room_valve_position_bath_trv"
    assert hass.states.get(actual).state == "39.0"
    hass.states.async_set("number.bath_trv_pi_heating_demand", "45", {"unit_of_measurement": "%"})
    await hass.async_block_till_done()
    assert hass.states.get(actual).state == "45.0"
    planned = hass.states.get(PLANNED).attributes
    assert planned["radiator_output_w"] is None
    assert planned["feed_forward"] is None
    assert planned["feed_forward_missing"] == ["radiator_output"]


async def test_room_menu_offers_thermostat_actions(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-014"""
    entry, room_id = await house_with_room(hass)

    def menu() -> Any:
        return hass.config_entries.subentries.async_init(
            (entry.entry_id, "room"), context={"source": SOURCE_RECONFIGURE, "subentry_id": room_id}
        )

    # ACT-060: an empty room may get thermostats or heaters.
    assert (await menu())["menu_options"] == ["edit_room", "add_thermostat", "add_heater"]
    await assign(hass, entry.entry_id, room_id, sonoff(hass), None)
    assert (await menu())["menu_options"] == [
        "edit_room",
        "add_thermostat",
        "edit_thermostat",
        "remove_thermostat",
    ]
    types = {s.subentry_type for s in entry.subentries.values()}
    assert types == {"room"}  # no separate thermostat entries any more


async def test_remove_thermostat_from_room(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-015"""
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), None)
    assert hass.states.get("sensor.living_room_kind_living_trv") is not None
    (thermostat_id,) = thermostat_ids(entry)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_RECONFIGURE, "subentry_id": room_id}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "remove_thermostat"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"thermostat": thermostat_id}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert thermostat_ids(entry) == []
    assert hass.states.get("sensor.living_room_kind_living_trv") is None


async def test_unknown_device_uses_setpoint_kind(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-004"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})

    roles_form = await assign(hass, entry.entry_id, room_id, device_id, None)

    assert roles_form["description_placeholders"]["profile"] == "-"
    assert suggested(roles_form) == {"climate": "climate.old_trv_climate"}
    assert hass.states.get("sensor.living_room_kind_old_trv").state == "setpoint"
    assert hass.states.get(PLANNED).attributes["strategies"] == ["setpoint"]


async def test_plan_follows_stop_and_safety(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-THERMO-005"""
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.home_central_mode", "option": "stop"},
        blocking=True,
    )
    assert hass.states.get(PLANNED).state == "0.0"
    assert hass.states.get(PLANNED).attributes["limits"] == ["stopped"]

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.home_central_mode", "option": "auto"},
        blocking=True,
    )
    hass.states.async_set(ROOM_SENSOR, "unavailable")
    freezer.tick(timedelta(minutes=16))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(PLANNED).state == "40.0"
    assert hass.states.get(PLANNED).attributes["limits"] == ["safety"]


async def test_plan_is_correct_right_after_restart(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-006"""
    # The restore cache must exist before the first entities register, else their removal on
    # reload fails depending on which tests ran before.
    mock_restore_cache(hass, [State("select.home_central_mode", "auto")])
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    reasons: list[str] = []
    async_track_state_change_event(
        hass,
        ["sensor.living_room_active_reason"],
        lambda event: reasons.append(event.data["new_state"].state),
    )

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert "safety_sensor_stale" not in reasons

    planned = hass.states.get(PLANNED)
    assert planned.attributes["limits"] != ["safety"]
    assert float(planned.state) == pytest.approx(72, abs=1)


async def test_roles_may_come_from_another_device(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-007"""
    entry, room_id = await house_with_room(hass)
    climate_device = z2m_device(
        hass, "Room climate Roy", "Bosch", "Room climate", {"climate": ("climate", "heat")}
    )
    z2m_device(hass, "Roy TRV", "Bosch", "TRV", {"valve_tappet": ("sensor", "24", "%")})

    result = await start_thermostat(hass, entry.entry_id, room_id, climate_device)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "climate": "climate.room_climate_roy_climate",
            "valve_read": "sensor.roy_trv_valve_tappet",
        },
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert hass.states.get("sensor.living_room_valve_position_room_climate_roy").state == "24.0"
    assert hass.states.get("sensor.living_room_kind_room_climate_roy").state == "setpoint"


async def test_reconfigure_thermostat(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-008"""
    entry, room_id = await house_with_room(hass)
    device_id = sonoff(hass)
    await assign(hass, entry.entry_id, room_id, device_id, 2000.0)
    (thermostat_id,) = thermostat_ids(entry)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_RECONFIGURE, "subentry_id": room_id}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "edit_thermostat"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"thermostat": thermostat_id}
    )
    assert result["step_id"] == "thermostat"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"device": device_id, "rated_output": 1500.0}
    )
    assert result["step_id"] == "roles"
    assert suggested(result)["valve_write"] == "number.living_trv_valve_opening_degree"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], suggested(result)
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    kind = hass.states.get("sensor.living_room_kind_living_trv")
    assert kind.attributes["radiator_output_w"] == 1500.0


async def test_implausible_role_is_rejected(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-009"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(
        hass,
        "Roy TRV",
        "Bosch",
        "TRV",
        {"climate": ("climate", "heat"), "temperature": ("sensor", "24.4", "°C")},
    )
    result = await start_thermostat(hass, entry.entry_id, room_id, device_id)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"climate": "climate.roy_trv_climate", "valve_read": "sensor.roy_trv_temperature"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"valve_read": "role_needs_percent"}


async def test_valve_strategy_needs_a_writable_valve(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-012"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})
    result = await start_thermostat(hass, entry.entry_id, room_id, device_id)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**suggested(result), "strategy": "valve"}
    )

    assert result["errors"] == {"strategy": "valve_strategy_needs_valve_write"}


async def test_return_sensor_sets_the_spread(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-013"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    hass.states.async_set(RETURN_SENSOR, "33.0", {"device_class": "temperature"})
    entry = await setup_house(
        hass,
        {
            **HOUSE_WITH_LOAD,
            "flow_temperature_entity": FLOW_SENSOR,
            "return_temperature_entity": RETURN_SENSOR,
        },
        [LIVING_ROOM],
    )
    room_id = next(iter(entry.subentries))
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})
    await assign(hass, entry.entry_id, room_id, device_id, 1500.0)

    planned = hass.states.get(PLANNED).attributes
    assert planned["return_temperature_used"] == 33.0
    assert planned["spread_used"] == 7.0


async def test_sonoff_shows_derived_valve_position(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-017"""
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    hass.states.async_set(
        "number.living_trv_valve_opening_degree", "43", {"unit_of_measurement": "%"}
    )
    hass.states.async_set(
        "number.living_trv_valve_closing_degree", "70", {"unit_of_measurement": "%"}
    )

    hass.states.async_set("climate.living_trv_climate", "heat", {"hvac_action": "heating"})
    await hass.async_block_till_done()
    valve = hass.states.get("sensor.living_room_valve_position_living_trv")
    assert float(valve.state) == 43.0
    assert valve.attributes["source"] == "derived"
    assert valve.attributes["hvac_action"] == "heating"

    hass.states.async_set("climate.living_trv_climate", "heat", {"hvac_action": "idle"})
    await hass.async_block_till_done()
    assert float(hass.states.get("sensor.living_room_valve_position_living_trv").state) == 30.0


async def test_stale_entities_are_removed(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-018"""
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    registry = er.async_get(hass)
    (thermostat_id,) = thermostat_ids(entry)
    stale = registry.async_get_or_create(
        "sensor", "thermogeist", f"{thermostat_id}_gone", config_entry=entry
    )
    before = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    after = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert after == before - {stale.entity_id}


async def test_written_valve_is_no_read_position(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-019"""
    entry, room_id = await house_with_room(hass)
    result = await start_thermostat(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    answers = suggested(result)
    answers["valve_read"] = answers["valve_write"]

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], answers)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"valve_read": "valve_read_is_write"}


async def test_feed_forward_ignores_a_warm_room(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-CTL-018"""
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    before = hass.states.get(PLANNED).attributes["feed_forward"]

    report_room_temperature(hass, 22.0)
    freezer.tick(timedelta(minutes=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(PLANNED).attributes["feed_forward"] == pytest.approx(before, abs=0.1)


@pytest.mark.parametrize("expected_lingering_timers", [True])  # MQTT test client
async def test_unknown_thermostat_is_detected_from_z2m(
    hass: HomeAssistant, mqtt_mock: Any, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-020"""
    entry, room_id = await house_with_room(hass)
    device_id = z2m_device(
        hass,
        "Hall TRV",
        "Acme",
        "TRV-42",
        {
            "climate": ("climate", "heat"),
            "valve_opening_degree": ("number", "100", "%"),
            "valve_closing_degree": ("number", "100", "%"),
            "external_temperature_input": ("number", "20", "°C"),
        },
    )
    device = dr.async_get(hass).async_get(device_id)
    ieee = next(i for d, i in device.identifiers if d == "mqtt").removeprefix("zigbee2mqtt_")
    exposes = [
        {"type": "numeric", "name": "valve_opening_degree", "access": 7, "unit": "%"},
        {"type": "numeric", "name": "valve_closing_degree", "access": 7, "unit": "%"},
        {"type": "numeric", "name": "external_temperature_input", "access": 7, "unit": "°C"},
    ]
    payload = [{"ieee_address": ieee, "supported": True, "definition": {"exposes": exposes}}]
    async_fire_mqtt_message(hass, "zigbee2mqtt/bridge/devices", json.dumps(payload))
    await hass.async_block_till_done()

    roles_form = await start_thermostat(hass, entry.entry_id, room_id, device_id, 1500.0)

    assert roles_form["description_placeholders"]["profile"] == (
        "Detected from Zigbee2MQTT (not tested)"
    )
    roles = suggested(roles_form)
    assert roles["valve_write"] == "number.hall_trv_valve_opening_degree"
    assert roles["valve_min"] == "number.hall_trv_valve_closing_degree"
    assert roles["external_temperature"] == "number.hall_trv_external_temperature_input"
