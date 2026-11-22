# SPDX-License-Identifier: MIT
"""Controller state across restarts (CTL-040) and moving thermostats into rooms (HAI-007)."""

from typing import Any

import pytest
from homeassistant.config_entries import ConfigSubentry, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.thermogeist.const import DOMAIN

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, setup_house
from .test_thermostats import FLOW_SENSOR, PLANNED, assign, z2m_device


async def test_integral_is_restored_after_restart(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-CONTROL-013"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [LIVING_ROOM]
    )
    room_id = next(iter(entry.subentries))
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})
    await assign(hass, entry.entry_id, room_id, device_id, 1500.0)
    # The running house has learned a correction and planned 46 % ...
    controller = entry.runtime_data.rooms[room_id].controller
    controller.state.integral_pct = -4.0
    controller.state.last_output_pct = 46.0
    controller.state.last_reported_pct = 46.0

    # ... a reload writes it and the new start reads it back (CTL-040).
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(PLANNED).attributes["integral"] == -4.0
    # CTL-040: the plan continues from the stored position, rate-limited.
    assert float(hass.states.get(PLANNED).state) == pytest.approx(46.0, abs=1)


async def test_changed_valves_start_fresh(
    hass: HomeAssistant, hass_storage: dict[str, Any], outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-CTL-017"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [LIVING_ROOM]
    )
    room_id = next(iter(entry.subentries))
    device_id = z2m_device(hass, "Old TRV", "Acme", "X1", {"climate": ("climate", "heat")})
    hass_storage[f"{DOMAIN}.{entry.entry_id}"] = {
        "version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}",
        "data": {
            "saved_at": dt_util.utcnow().isoformat(),
            "controller": {
                room_id: {
                    "integral_pct": -4.0,
                    "integral_has_start_bias": False,
                    "min_opening_relaxed": False,
                }
            },
            "controller_hardware": {room_id: "another-device|automatic|False|climate=x"},
        },
    }

    await assign(hass, entry.entry_id, room_id, device_id, 1500.0)  # reloads the house

    assert hass.states.get(PLANNED).attributes["integral"] != -4.0


async def test_thermostat_subentries_move_into_their_room(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-THERMO-016"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        minor_version=1,
        data=HOUSE_WITH_LOAD,
        subentries_data=[
            ConfigSubentryData(
                data=LIVING_ROOM, subentry_type="room", title="Living room", unique_id=None
            )
        ],
    )
    entry.add_to_hass(hass)
    room_id = next(iter(entry.subentries))
    thermostat_data = {
        "room": room_id,
        "device": None,
        "roles": {"climate": "climate.old_trv_climate"},
        "rated_output": 700.0,
        "strategy": "automatic",
    }
    hass.config_entries.async_add_subentry(
        entry,
        ConfigSubentry(
            data=thermostat_data, subentry_type="thermostat", title="Old TRV", unique_id=None
        ),
    )
    thermostat_id = next(s for s, e in entry.subentries.items() if e.subentry_type == "thermostat")
    er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, f"{thermostat_id}_thermostat_kind", config_entry=entry
    )
    hass.states.async_set("climate.old_trv_climate", "heat", {"temperature": 20.0})

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 2
    assert {s.subentry_type for s in entry.subentries.values()} == {"room"}
    moved = entry.subentries[room_id].data["thermostats"][thermostat_id]
    assert moved["name"] == "Old TRV"
    assert moved["rated_output"] == 700.0
    assert "room" not in moved
    kind = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{thermostat_id}_thermostat_kind"
    )
    assert kind is not None and hass.states.get(kind).state == "setpoint"
