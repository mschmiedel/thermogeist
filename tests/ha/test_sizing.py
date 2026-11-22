# SPDX-License-Identifier: MIT
"""Radiator size per room in Home Assistant (spec DIA-010 to DIA-015)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.thermogeist.const import DOMAIN

from .conftest import (
    HOUSE_WITH_LOAD,
    LIVING_ROOM,
    OUTDOOR_SENSOR,
    report_room_temperature,
    setup_house,
)
from .test_thermostats import FLOW_SENSOR, assign, house_with_room, z2m_device

SIZE = "sensor.living_room_radiator_size"
DESIGN_FLOW = "sensor.home_flow_on_the_design_day"


def learned_curve(hours: int = 60) -> list[list[Any]]:
    """A heat pump whose flow follows 35 °C - 0.6 x outdoor, outdoor 2-12 °C."""
    now = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    rows = []
    for i in range(hours):
        outdoor = 2.0 + 10.0 * i / (hours - 1)
        hour = now - timedelta(hours=hours - i)
        rows.append([hour.isoformat(), outdoor, 35.0 - 0.6 * outdoor])
    return rows


async def store(hass_storage: dict[str, Any], entry: Any, sizing: dict[str, Any]) -> None:
    """Stored data, also loaded into the running house: a reload writes its state first."""
    hass_storage[f"{DOMAIN}.{entry.entry_id}"] = {
        "version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}",
        "data": {"sizing": sizing},
    }
    await entry.runtime_data.async_load()


def plain_trv(hass: HomeAssistant, name: str) -> str:
    return z2m_device(hass, name, "Acme", "X1", {"climate": ("climate", "heat")})


async def test_undersized_room_sensor_and_issue(
    hass: HomeAssistant, hass_storage: dict[str, Any], outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-SIZING-005"""
    entry, room_id = await house_with_room(hass)
    await store(hass_storage, entry, {"curve": learned_curve()})

    await assign(hass, entry.entry_id, room_id, plain_trv(hass, "Small TRV"), 300.0)

    size = hass.states.get(SIZE)
    assert size.state == "undersized"
    assert size.attributes["cause"] == "radiator_small"
    assert size.attributes["basis"] == "static"
    assert size.attributes["load_pct"] > 100
    assert float(hass.states.get(DESIGN_FLOW).state) == 41.3
    assert hass.states.get(DESIGN_FLOW).attributes["hours"] == 60
    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"radiator_undersized_{room_id}")
    assert issue is not None
    assert issue.learn_more_url.endswith("/en/faq/radiator_sizing.md")

    await entry.runtime_data.async_save()
    await assign(hass, entry.entry_id, room_id, plain_trv(hass, "Big TRV"), 6000.0)

    assert hass.states.get(SIZE).state == "right_size"
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"radiator_undersized_{room_id}") is None


async def test_hours_are_collected_and_saved(
    hass: HomeAssistant, outdoor_sensor: str, room_sensor: str, freezer: FrozenDateTimeFactory
) -> None:
    """Scenario: SCN-SIZING-006"""
    freezer.move_to(datetime(2026, 11, 20, 10, 0, 30, tzinfo=UTC))
    hass.states.async_set(OUTDOOR_SENSOR, "2.0", {"device_class": "temperature"})
    report_room_temperature(hass, 19.0)
    entry, room_id = await house_with_room(hass)
    bosch = z2m_device(
        hass,
        "Bath TRV",
        "Bosch",
        "BTH-RA",
        {"climate": ("climate", "heat"), "pi_heating_demand": ("number", "100", "%")},
    )
    await assign(hass, entry.entry_id, room_id, bosch, 1000.0)

    for _ in range(61):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    runtime = entry.runtime_data
    assert len(runtime.curve_hours) == 1
    assert runtime.curve_hours[0].flow_c == 40.0
    assert hass.states.get(SIZE).attributes["full_open_hours"] == 1

    await runtime.async_save()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(SIZE).attributes["full_open_hours"] == 1
    assert len(entry.runtime_data.curve_hours) == 1


async def test_oversized_rooms(
    hass: HomeAssistant, hass_storage: dict[str, Any], outdoor_sensor: str, room_sensor: str
) -> None:
    """Scenario: SCN-SIZING-007"""
    hass.states.async_set(FLOW_SENSOR, "40.0", {"device_class": "temperature"})
    office = {**LIVING_ROOM, "name": "Office"}
    for heating_type in ("heat_pump", "boiler"):
        entry = await setup_house(
            hass,
            {
                **HOUSE_WITH_LOAD,
                "heating_type": heating_type,
                "flow_temperature_entity": FLOW_SENSOR,
            },
            [LIVING_ROOM, office],
        )
        await store(hass_storage, entry, {"curve": learned_curve()})
        room_ids = list(entry.subentries)
        for number, room_id in enumerate(room_ids):
            await assign(
                hass, entry.entry_id, room_id, plain_trv(hass, f"{heating_type} {number}"), 10000.0
            )
        registry = ir.async_get(hass)
        size = hass.states.get(SIZE).attributes
        assert hass.states.get(SIZE).state == "heavily_oversized"
        assert size["cause"] == "flow_high"
        assert registry.async_get_issue(DOMAIN, "flow_higher_than_needed") is not None
        room_issues = [
            registry.async_get_issue(DOMAIN, f"radiator_oversized_{room_id}")
            for room_id in room_ids
        ]
        if heating_type == "heat_pump":
            assert size["note"] == "reserve"
            assert room_issues == [None, None]
        else:
            assert "note" not in size
            assert all(issue is not None for issue in room_issues)
        assert await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()
