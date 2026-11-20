# SPDX-License-Identifier: MIT
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant, State
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
)

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, setup_house

FLOW_SENSOR = "sensor.flow_temperature"
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
    for expose, (domain, state) in exposes.items():
        entity = registry.async_get_or_create(
            domain,
            "mqtt",
            f"{ieee}_{expose}_zigbee2mqtt",
            device_id=device.id,
            config_entry=mqtt,
            suggested_object_id=f"{name.lower().replace(' ', '_')}_{expose}",
        )
        hass.states.async_set(entity.entity_id, state)
    return device.id


def sonoff(hass: HomeAssistant) -> str:
    return z2m_device(
        hass,
        "Living TRV",
        "SONOFF",
        "TRVZB",
        {
            "climate": ("climate", "heat"),
            "valve_opening_degree": ("number", "100"),
            "valve_closing_degree": ("number", "100"),
            "external_temperature_input": ("number", "20"),
            "child_lock": ("switch", "off"),
        },
    )


def suggested(result: dict[str, Any]) -> dict[str, str]:
    values = {}
    for marker in result["data_schema"].schema:
        description = marker.description or {}
        if description.get("suggested_value"):
            values[str(marker)] = description["suggested_value"]
    return values


async def assign(
    hass: HomeAssistant, entry_id: str, room_id: str, device_id: str, rated: float | None
) -> dict[str, Any]:
    result = await hass.config_entries.subentries.async_init(
        (entry_id, "thermostat"), context={"source": SOURCE_USER}
    )
    answers: dict[str, Any] = {"room": room_id, "device": device_id}
    if rated is not None:
        answers["rated_output"] = rated
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], answers)
    assert result["step_id"] == "roles"
    roles_form = result
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], suggested(result)
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
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
    assert planned.attributes["feed_forward"] == pytest.approx(60.6, abs=0.5)
    assert planned.attributes["feed_forward_missing"] == []
    assert float(planned.state) == pytest.approx(68, abs=1)
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
        {"climate": ("climate", "heat"), "pi_heating_demand": ("number", "39")},
    )

    roles_form = await assign(hass, entry.entry_id, room_id, device_id, None)

    assert roles_form["description_placeholders"]["profile"].startswith("Bosch")
    actual = "sensor.living_room_valve_position_bath_trv"
    assert hass.states.get(actual).state == "39.0"
    hass.states.async_set("number.bath_trv_pi_heating_demand", "45")
    await hass.async_block_till_done()
    assert hass.states.get(actual).state == "45.0"
    planned = hass.states.get(PLANNED).attributes
    assert planned["radiator_output_w"] is None
    assert planned["feed_forward"] is None
    assert planned["feed_forward_missing"] == ["radiator_output"]


async def test_thermostat_needs_a_room(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-THERMO-003"""
    entry = await setup_house(hass)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "thermostat"), context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_rooms"


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
    freezer.tick(timedelta(minutes=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(PLANNED).state == "40.0"
    assert hass.states.get(PLANNED).attributes["limits"] == ["safety"]


async def test_plan_is_correct_right_after_restart(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-006"""
    entry, room_id = await house_with_room(hass)
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    mock_restore_cache(hass, [State("select.home_central_mode", "auto")])
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
    assert float(planned.state) == pytest.approx(68, abs=1)


async def test_roles_may_come_from_another_device(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-007"""
    entry, room_id = await house_with_room(hass)
    climate_device = z2m_device(
        hass, "Room climate Roy", "Bosch", "Room climate", {"climate": ("climate", "heat")}
    )
    z2m_device(hass, "Roy TRV", "Bosch", "TRV", {"valve_tappet": ("sensor", "24")})

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "thermostat"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"room": room_id, "device": climate_device}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "climate": "climate.room_climate_roy_climate",
            "valve_read": "sensor.roy_trv_valve_tappet",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert hass.states.get("sensor.living_room_valve_position_room_climate_roy").state == "24.0"
    assert hass.states.get("sensor.living_room_kind_room_climate_roy").state == "setpoint"


async def test_reconfigure_thermostat(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-008"""
    entry, room_id = await house_with_room(hass)
    device_id = sonoff(hass)
    await assign(hass, entry.entry_id, room_id, device_id, 2000.0)
    thermostat_id = next(
        sid for sid, s in entry.subentries.items() if s.subentry_type == "thermostat"
    )

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "thermostat"),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": thermostat_id},
    )
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"room": room_id, "device": device_id, "rated_output": 1500.0}
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
