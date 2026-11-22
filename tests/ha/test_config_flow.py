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
    return result


NONE = {"heat_load_known": "no", "flow_measurement": "none"}


async def test_minimal_setup_creates_house(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-001"""
    result = await _start_with_required(hass, REQUIRED)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], NONE)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert "heat_load_known" not in result["data"]
    assert hass.states.get("select.home_central_mode").state == "auto"
    assert hass.states.get("number.home_minimum_valve_opening").state == "40.0"
    assert hass.states.get("sensor.home_heating_type").state == "heat_pump"


async def test_heat_load_without_design_temperature_shows_error(
    hass: HomeAssistant, outdoor_sensor: str
) -> None:
    """Scenario: SCN-SETUP-002"""
    result = await _start_with_required(hass, REQUIRED)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**NONE, "heat_load_known": "yes"}
    )
    assert result["step_id"] == "heat_load"

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
    result = await hass.config_entries.flow.async_configure(result["flow_id"], NONE)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2
    assert hass.states.get("sensor.home_heating_type").state == "heat_pump"
    assert hass.states.get("sensor.granny_flat_heating_type").state == "boiler"


async def test_questions_decide_the_details(hass: HomeAssistant, outdoor_sensor: str) -> None:
    """Scenario: SCN-SETUP-008"""
    for name in ("sensor.flow", "sensor.return"):
        hass.states.async_set(name, "35", {"device_class": "temperature"})
    result = await _start_with_required(hass, REQUIRED)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"heat_load_known": "no", "flow_measurement": "flow_return"}
    )
    assert result["step_id"] == "flow"
    assert {str(k) for k in result["data_schema"].schema} == {
        "flow_temperature_entity",
        "return_temperature_entity",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"flow_temperature_entity": "sensor.flow", "return_temperature_entity": "sensor.return"},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = hass.config_entries.async_get_entry(result["result"].entry_id)

    # Options: the answers are pre-selected; "no flow measurement" clears both sensors.
    result = await hass.config_entries.options.async_init(entry.entry_id)
    defaults = {str(k): k.default() for k in result["data_schema"].schema if callable(k.default)}
    assert defaults["heat_load_known"] == "no"
    assert defaults["flow_measurement"] == "flow_return"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "heating_type": "heat_pump",
            "outdoor_temperature_entity": outdoor_sensor,
            "heat_load_known": "no",
            "flow_measurement": "none",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["flow_temperature_entity"] is None
    assert result["data"]["return_temperature_entity"] is None


async def test_heating_curve_instead_of_a_flow_sensor(
    hass: HomeAssistant, outdoor_sensor: str
) -> None:
    """Scenario: SCN-SETUP-009"""
    result = await _start_with_required(hass, REQUIRED)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"heat_load_known": "no", "flow_measurement": "curve"}
    )
    assert result["step_id"] == "heating_curve"
    assert {str(k) for k in result["data_schema"].schema} == {
        "curve_cold_outdoor",
        "curve_cold_flow",
        "curve_warm_outdoor",
        "curve_warm_flow",
    }
    curve = {
        "curve_cold_outdoor": -10.0,
        "curve_cold_flow": 45.0,
        "curve_warm_outdoor": 15.0,
        "curve_warm_flow": 30.0,
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**curve, "curve_warm_flow": 50.0}
    )
    assert result["errors"] == {"curve_warm_flow": "curve_flow_rises_when_warmer"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], curve)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = hass.config_entries.async_get_entry(result["result"].entry_id)
    assert {k: entry.data[k] for k in curve} == curve

    # Options: "curve" is pre-selected; choosing a flow sensor instead clears the curve.
    result = await hass.config_entries.options.async_init(entry.entry_id)
    defaults = {str(k): k.default() for k in result["data_schema"].schema if callable(k.default)}
    assert defaults["flow_measurement"] == "curve"
    hass.states.async_set("sensor.flow", "35", {"device_class": "temperature"})
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "heating_type": "heat_pump",
            "outdoor_temperature_entity": outdoor_sensor,
            "heat_load_known": "no",
            "flow_measurement": "flow",
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"flow_temperature_entity": "sensor.flow"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert all(result["data"][k] is None for k in curve)
