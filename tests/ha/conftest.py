# SPDX-License-Identifier: MIT
"""Fixtures for tests that run inside a real Home Assistant instance."""

from typing import Any

import pytest
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.thermogeist.const import DOMAIN

OUTDOOR_SENSOR = "sensor.outdoor"

REQUIRED: dict[str, Any] = {
    "name": "Home",
    "heating_type": "heat_pump",
    "outdoor_temperature_entity": OUTDOOR_SENSOR,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading Thermogeist from custom_components in every HA test."""


@pytest.fixture
def outdoor_sensor(hass: HomeAssistant) -> str:
    hass.states.async_set(
        OUTDOOR_SENSOR, "5.0", {"device_class": "temperature", "unit_of_measurement": "°C"}
    )
    return OUTDOOR_SENSOR


ROOM_SENSOR = "sensor.living_room_temperature"

HOUSE_WITH_LOAD: dict[str, Any] = {
    **REQUIRED,
    "heat_load": 6.5,
    "design_outdoor_temperature": -10.5,
    "living_area": 160.0,
}

LIVING_ROOM: dict[str, Any] = {
    "name": "Living room",
    "temperature_entity": ROOM_SENSOR,
    "share_mode": "estimated",
    "floor_area": 20.0,
    "ceiling_height": 2.5,
    "exterior_walls": 2,
    "above": "heated",
    "below": "heated",
}


@pytest.fixture
def room_sensor(hass: HomeAssistant) -> str:
    report_room_temperature(hass, 19.5)
    return ROOM_SENSOR


def report_room_temperature(hass: HomeAssistant, value: float) -> None:
    hass.states.async_set(
        ROOM_SENSOR,
        str(value),
        {"device_class": "temperature", "unit_of_measurement": "°C"},
        force_update=True,
    )


async def setup_house(
    hass: HomeAssistant,
    data: dict[str, Any] | None = None,
    rooms: list[dict[str, Any]] | None = None,
) -> MockConfigEntry:
    """Create and load a house entry directly, skipping the dialog."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        minor_version=2,
        data=data or REQUIRED,
        subentries_data=[
            ConfigSubentryData(data=room, subentry_type="room", title=room["name"], unique_id=None)
            for room in rooms or []
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
