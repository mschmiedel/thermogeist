# SPDX-License-Identifier: MIT
"""Fixtures for tests that run inside a real Home Assistant instance."""

from typing import Any

import pytest
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


async def setup_house(hass: HomeAssistant, data: dict[str, Any] | None = None) -> MockConfigEntry:
    """Create and load a house entry directly, skipping the dialog."""
    entry = MockConfigEntry(domain=DOMAIN, title="Home", data=data or REQUIRED)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
