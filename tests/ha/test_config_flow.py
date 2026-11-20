# SPDX-License-Identifier: MIT
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.thermogeist.const import DOMAIN

from .conftest import REQUIRED, setup_house


async def _start_with_required(hass: HomeAssistant, answers: dict) -> dict:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["last_step"] is False  # button reads "Next"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], answers)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "details"
    assert result["last_step"] is True
    return result


async def test_minimal_setup_creates_house(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-001"""
    result = await _start_with_required(hass, REQUIRED)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert hass.states.get("select.home_central_mode").state == "auto"
    assert hass.states.get("number.home_minimum_valve_opening").state == "40.0"
    assert hass.states.get("sensor.home_heating_type").state == "heat_pump"


async def test_heat_load_without_design_temperature_shows_error(
    hass: HomeAssistant, outdoor_sensor: str
) -> None:
    """Scenario: SCN-SETUP-002"""
    result = await _start_with_required(hass, REQUIRED)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"heat_load": 8.0})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"design_outdoor_temperature": "design_temperature_required"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"heat_load": 8.0, "design_outdoor_temperature": -12.0}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["heat_load"] == 8.0
    assert result["data"]["design_outdoor_temperature"] == -12.0
    assert hass.states.get("sensor.home_heat_load").state == "8.0"


async def test_options_change_heating_type(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-003"""
    entry = await setup_house(hass)
    assert hass.states.get("number.home_minimum_valve_opening").state == "40.0"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"heating_type": "boiler", "outdoor_temperature_entity": outdoor_sensor},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert hass.states.get("sensor.home_heating_type").state == "boiler"
    assert hass.states.get("number.home_minimum_valve_opening").state == "0.0"


async def test_two_houses_can_be_added(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-005"""
    await setup_house(hass)

    result = await _start_with_required(
        hass, {**REQUIRED, "name": "Granny flat", "heating_type": "boiler"}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2
    assert hass.states.get("sensor.home_heating_type").state == "heat_pump"
    assert hass.states.get("sensor.granny_flat_heating_type").state == "boiler"
