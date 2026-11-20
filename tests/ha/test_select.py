# SPDX-License-Identifier: MIT
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import mock_restore_cache

from .conftest import setup_house


async def test_central_mode_is_restored(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-004"""
    mock_restore_cache(hass, [State("select.home_central_mode", "frost_protection")])

    await setup_house(hass)

    assert hass.states.get("select.home_central_mode").state == "frost_protection"


async def test_central_mode_can_be_changed(hass: HomeAssistant, outdoor_sensor: str) -> None:
    await setup_house(hass)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.home_central_mode", "option": "stop"},
        blocking=True,
    )

    assert hass.states.get("select.home_central_mode").state == "stop"
