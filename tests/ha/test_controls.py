# SPDX-License-Identifier: MIT
from homeassistant.core import HomeAssistant

from .conftest import setup_house

MIN_OPENING = "number.home_minimum_valve_opening"
DEAD_BAND = "number.home_dead_band"
RESET = "button.home_reset_control_settings_to_profile"


async def _set(hass: HomeAssistant, entity_id: str, value: float) -> None:
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": value}, blocking=True
    )


async def test_override_persists_and_survives_heating_type_change(
    hass: HomeAssistant, outdoor_sensor: str
) -> None:
    """Scenario: SCN-SETUP-006"""
    entry = await setup_house(hass)
    assert hass.states.get(MIN_OPENING).attributes["source"] == "profile"

    await _set(hass, MIN_OPENING, 30)
    assert hass.states.get(MIN_OPENING).state == "30.0"
    assert hass.states.get(MIN_OPENING).attributes["source"] == "user"

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(MIN_OPENING).state == "30.0"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"heating_type": "boiler", "outdoor_temperature_entity": outdoor_sensor},
    )
    await hass.async_block_till_done()
    assert hass.states.get(MIN_OPENING).state == "30.0"
    assert hass.states.get(DEAD_BAND).state == "0.2"
    assert hass.states.get(DEAD_BAND).attributes["source"] == "profile"


async def test_reset_restores_profile(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-007"""
    await setup_house(hass)
    await _set(hass, MIN_OPENING, 30)

    await hass.services.async_call("button", "press", {"entity_id": RESET}, blocking=True)

    assert hass.states.get(MIN_OPENING).state == "40.0"
    assert hass.states.get(MIN_OPENING).attributes["source"] == "profile"
