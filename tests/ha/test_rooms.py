# SPDX-License-Identifier: MIT
from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
)

from .conftest import (
    HOUSE_WITH_LOAD,
    LIVING_ROOM,
    ROOM_SENSOR,
    finish_new_room,
    report_room_temperature,
    setup_house,
)
from .test_thermostats import sonoff, suggested

CLIMATE = "climate.living_room"
REASON = "sensor.living_room_active_reason"
TARGET = "sensor.living_room_target_temperature"
DEMAND = "sensor.living_room_heat_demand"
SHARE = "sensor.living_room_share_of_heat_load"
HEAT_LOSS = "sensor.living_room_heat_loss_coefficient"
UNASSIGNED = "sensor.home_heat_load_not_assigned_to_a_room"


def state(hass: HomeAssistant, entity_id: str) -> str:
    current = hass.states.get(entity_id)
    assert current is not None, f"{entity_id} missing"
    return current.state


async def _add_room(hass: HomeAssistant, entry_id: str, basics: dict, step2: dict) -> dict:
    result = await hass.config_entries.subentries.async_init(
        (entry_id, "room"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], step2)
    return await finish_new_room(hass, result)


async def test_add_estimated_room(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-001"""
    entry = await setup_house(hass, HOUSE_WITH_LOAD)
    basics = {k: LIVING_ROOM[k] for k in ("name", "temperature_entity", "share_mode")}
    geometry = {k: v for k, v in LIVING_ROOM.items() if k not in basics}

    result = await _add_room(hass, entry.entry_id, basics, geometry)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "room_saved"
    climate = hass.states.get(CLIMATE)
    assert climate.attributes["current_temperature"] == 19.5
    assert climate.attributes["temperature"] == 20.0
    assert float(state(hass, SHARE)) == pytest.approx(12.5)
    assert float(state(hass, HEAT_LOSS)) == pytest.approx(812.5 / 30.5)
    assert float(state(hass, DEMAND)) == pytest.approx(812.5 / 30.5 * 15)
    assert state(hass, REASON) == "setpoint"
    assert float(state(hass, UNASSIGNED)) == pytest.approx(87.5)


async def test_known_share_over_total_is_rejected(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-002"""
    first = {**LIVING_ROOM, "share_mode": "known", "known_share": 60.0}
    entry = await setup_house(hass, {**HOUSE_WITH_LOAD, "share_outside": 10.0}, [first])
    basics = {"name": "Office", "temperature_entity": room_sensor, "share_mode": "known"}

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    assert result["step_id"] == "known_share"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"known_share": 35.0}
    )
    assert result["errors"] == {"known_share": "known_shares_exceed_total"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"known_share": 30.0}
    )
    result = await finish_new_room(hass, result)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "room_saved"


async def test_silent_sensor_is_reported(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-003"""
    await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])
    assert state(hass, REASON) == "setpoint"

    # A sensor that only reports changes may stay quiet for hours.
    freezer.tick(timedelta(hours=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert state(hass, REASON) == "setpoint"

    hass.states.async_set(ROOM_SENSOR, "unavailable")
    freezer.tick(timedelta(minutes=14))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert state(hass, REASON) == "setpoint"

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert state(hass, REASON) == "safety_sensor_stale"
    assert hass.states.get(REASON).attributes["cause"] == "unavailable"
    assert hass.states.get(REASON).attributes["severity"] == "safety"

    report_room_temperature(hass, 19.6)
    await hass.async_block_till_done()
    assert state(hass, REASON) == "setpoint"


async def test_central_mode_reaches_rooms(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-004"""
    await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])

    async def central(option: str) -> None:
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.home_central_mode", "option": option},
            blocking=True,
        )

    await central("stop")
    assert state(hass, REASON) == "central_stop"
    assert state(hass, TARGET) == "unknown"
    assert state(hass, DEMAND) == "unknown"

    await central("frost_protection")
    assert state(hass, REASON) == "frost_protection"
    assert float(state(hass, TARGET)) == 7.0

    await central("auto")
    assert state(hass, REASON) == "setpoint"
    assert float(state(hass, TARGET)) == 20.0


async def test_setpoint_survives_reload(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-005"""
    entry = await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])

    await hass.services.async_call(
        "climate", "set_temperature", {"entity_id": CLIMATE, "temperature": 21.5}, blocking=True
    )
    assert hass.states.get(CLIMATE).attributes["temperature"] == 21.5

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(CLIMATE).attributes["temperature"] == 21.5
    assert float(state(hass, TARGET)) == 21.5


async def test_reconfigure_room(hass: HomeAssistant, outdoor_sensor: str, room_sensor: str) -> None:
    """Scenario: SCN-ROOMS-006"""
    entry = await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])
    subentry_id = next(iter(entry.subentries))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry_id},
    )
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "edit_room"}
    )
    assert result["step_id"] == "edit_room"
    basics = {k: LIVING_ROOM[k] for k in ("name", "temperature_entity", "share_mode")}
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    assert result["step_id"] == "geometry"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {**{k: v for k, v in LIVING_ROOM.items() if k not in basics}, "floor_area": 40.0},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert float(state(hass, SHARE)) == pytest.approx(25.0)


async def test_reason_is_not_rewritten_while_unchanged(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-ROOMS-007"""
    await setup_house(hass, HOUSE_WITH_LOAD, [LIVING_ROOM])
    since = hass.states.get(REASON).attributes["since"]
    changes = async_capture_events(hass, "state_changed")

    for _ in range(3):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert [e for e in changes if e.data["entity_id"] == REASON] == []
    assert hass.states.get(REASON).attributes["since"] == since


async def test_new_room_offers_thermostats(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-014"""
    entry = await setup_house(hass, HOUSE_WITH_LOAD)
    device_id = sonoff(hass)
    basics = {k: LIVING_ROOM[k] for k in ("name", "temperature_entity", "share_mode")}
    geometry = {k: v for k, v in LIVING_ROOM.items() if k not in basics}
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], geometry)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "new_room_thermostats"
    room = next(iter(entry.subentries.values()))  # saved already, without thermostats
    assert not room.data.get("thermostats")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "add_new_room_thermostat"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"device": device_id, "rated_output": 1500.0}
    )
    assert result["step_id"] == "roles"
    top = {str(m): v for m, v in result["data_schema"].schema.items()}
    assert "strategy" in top
    assert top["detected_roles"].options["collapsed"] is True
    # The frontend submits the pre-filled values, also from the collapsed section.
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], suggested(result)
    )
    assert result["step_id"] == "new_room_thermostats"
    assert result["description_placeholders"]["count"] == "1"

    result = await finish_new_room(hass, result)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "room_saved"
    assert len(entry.subentries) == 1
    room = next(iter(entry.subentries.values()))
    assert len(room.data["thermostats"]) == 1
    assert hass.states.get("sensor.living_room_planned_valve_position") is not None


async def test_cancelled_dialog_keeps_the_new_room(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-ROOMS-015"""
    entry = await setup_house(hass, HOUSE_WITH_LOAD)
    device_id = sonoff(hass)
    basics = {k: LIVING_ROOM[k] for k in ("name", "temperature_entity", "share_mode")}
    geometry = {k: v for k, v in LIVING_ROOM.items() if k not in basics}
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "room"), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], basics)
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], geometry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "add_new_room_thermostat"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"device": device_id}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], suggested(result)
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "add_new_room_thermostat"}
    )
    assert result["step_id"] == "thermostat"

    hass.config_entries.subentries.async_abort(result["flow_id"])  # the user closes the dialog
    await hass.async_block_till_done()

    rooms = list(entry.subentries.values())
    assert len(rooms) == 1
    assert rooms[0].title == LIVING_ROOM["name"]
    assert len(rooms[0].data["thermostats"]) == 1
    assert hass.states.get("sensor.living_room_planned_valve_position") is not None


async def test_weather_entity_as_outdoor_temperature(
    hass: HomeAssistant, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-HOUSE-010"""
    weather = "weather.forecast_home"
    hass.states.async_set(weather, "cloudy", {"temperature": 5.0, "temperature_unit": "°C"})
    await setup_house(
        hass, {**HOUSE_WITH_LOAD, "outdoor_temperature_entity": weather}, [LIVING_ROOM]
    )
    mild = float(state(hass, DEMAND))
    assert mild == pytest.approx(812.5 / 30.5 * 15)

    hass.states.async_set(weather, "cloudy", {"temperature": 0.0, "temperature_unit": "°C"})
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert float(state(hass, DEMAND)) == pytest.approx(812.5 / 30.5 * 20)
