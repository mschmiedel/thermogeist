# SPDX-License-Identifier: MIT
"""Learned demand in Home Assistant (spec LRN-034 to LRN-036)."""

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.thermogeist.core.learning import Observation

from .conftest import HOUSE_WITH_LOAD, LIVING_ROOM, report_room_temperature, setup_house
from .test_thermostats import FLOW_SENSOR, PLANNED, assign, sonoff

LEARNED = "sensor.living_room_learned_demand"
RESET = "button.living_room_learning_start_again"


async def test_feed_forward_uses_learned_demand(
    hass: HomeAssistant,
    outdoor_sensor: str,
    room_sensor: str,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Scenario: SCN-LRN-003"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [LIVING_ROOM]
    )
    room_id = next(iter(entry.subentries))
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    full = hass.states.get(PLANNED).attributes["feed_forward"]
    assert hass.states.get(LEARNED).attributes["state"] == "learning"

    now = dt_util.utcnow()
    # The running house has collected 30 quiet hours on 4 days; a reload writes and reads them.
    entry.runtime_data.rooms[room_id].learn_observations = [
        Observation(now - timedelta(days=i % 4, hours=i // 4), 0.5, True) for i in range(30)
    ]
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    learned = hass.states.get(LEARNED)
    assert learned.state == "50"
    assert learned.attributes["state"] == "settled"
    assert learned.attributes["quiet_hours"] == 30
    assert hass.states.get(PLANNED).attributes["feed_forward"] < full

    await hass.services.async_call("button", "press", {"entity_id": RESET}, blocking=True)
    assert hass.states.get(LEARNED).attributes["state"] == "learning"
    freezer.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(PLANNED).attributes["feed_forward"] == pytest.approx(full, abs=1)


async def test_quiet_hours_are_collected(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-LRN-004"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    entry = await setup_house(
        hass, {**HOUSE_WITH_LOAD, "flow_temperature_entity": FLOW_SENSOR}, [LIVING_ROOM]
    )
    room_id = next(iter(entry.subentries))
    await assign(hass, entry.entry_id, room_id, sonoff(hass), 2000.0)
    hass.states.async_set(
        "number.living_trv_valve_opening_degree", "40", {"unit_of_measurement": "%"}
    )
    hass.states.async_set(
        "number.living_trv_valve_closing_degree", "70", {"unit_of_measurement": "%"}
    )
    hass.states.async_set("climate.living_trv_climate", "heat", {"hvac_action": "heating"})

    for _ in range(4 * 60):
        report_room_temperature(hass, 20.0)
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert entry.runtime_data.rooms[room_id].learn_observations
    assert hass.states.get(LEARNED).attributes["quiet_hours"] >= 1

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.rooms[room_id].learn_observations
