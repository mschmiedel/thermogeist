# SPDX-License-Identifier: MIT
import json
from datetime import timedelta
from pathlib import Path

from custom_components.thermogeist.core.actuator import (
    DeviceEntity,
    EntityFacts,
    Kind,
    Role,
    check_role,
    derived_valve_pct,
    derives_valve,
    find_profile,
    kind_for,
    parse_profile,
    resolve_roles,
)

PROFILE_DIR = (
    Path(__file__).parent.parent.parent / "custom_components" / "thermogeist" / "device_profiles"
)
PROFILES = [parse_profile(json.loads(p.read_text())) for p in sorted(PROFILE_DIR.glob("*.json"))]
IEEE = "0x00124b0029aabbcc"


def z2m(domain: str, expose: str) -> DeviceEntity:
    return DeviceEntity(
        entity_id=f"{domain}.bath_{expose}", unique_id=f"{IEEE}_{expose}_zigbee2mqtt", domain=domain
    )


def test_profiles_match_by_manufacturer_and_model_id() -> None:
    """Scenario: SCN-ACT-001"""
    assert {p.profile_id for p in PROFILES} == {"sonoff_trvzb", "sonoff_trv_zbt", "bosch_bth_ra"}
    assert find_profile(PROFILES, "SONOFF", "TRVZB").profile_id == "sonoff_trvzb"
    assert find_profile(PROFILES, "Bosch", "bth-ra").profile_id == "bosch_bth_ra"
    assert find_profile(PROFILES, "Acme", "TRVZB") is None
    assert find_profile(PROFILES, "SONOFF", None) is None


def test_sonoff_roles_are_resolved_from_z2m_unique_ids() -> None:
    """Scenario: SCN-ACT-002"""
    entities = [
        z2m("climate", "climate"),
        z2m("number", "valve_opening_degree"),
        z2m("number", "valve_closing_degree"),
        z2m("number", "external_temperature_input"),
        z2m("switch", "child_lock"),
        z2m("sensor", "battery"),
    ]
    profile = find_profile(PROFILES, "SONOFF", "TRVZB")

    roles = resolve_roles(entities, profile)

    assert roles == {
        Role.CLIMATE: "climate.bath_climate",
        Role.VALVE_WRITE: "number.bath_valve_opening_degree",
        Role.VALVE_MIN: "number.bath_valve_closing_degree",
        Role.EXTERNAL_TEMPERATURE: "number.bath_external_temperature_input",
        Role.CHILD_LOCK: "switch.bath_child_lock",
    }
    assert profile.roles["z2m"][Role.VALVE_MIN].inverted
    assert kind_for(roles) is Kind.VALVE


def test_bosch_uses_one_entity_to_read_and_write_the_valve() -> None:
    """Scenario: SCN-ACT-003"""
    entities = [z2m("climate", "climate"), z2m("number", "pi_heating_demand")]

    roles = resolve_roles(entities, find_profile(PROFILES, "Bosch", "BTH-RA"))

    assert roles[Role.VALVE_READ] == roles[Role.VALVE_WRITE] == "number.bath_pi_heating_demand"
    assert Role.VALVE_MIN not in roles


def test_unknown_device_falls_back_to_setpoint_kind() -> None:
    """Scenario: SCN-ACT-004"""
    entities = [DeviceEntity("climate.office", "abc", "climate")]

    roles = resolve_roles(entities, None)

    assert roles == {Role.CLIMATE: "climate.office"}
    assert kind_for(roles) is Kind.SETPOINT


def test_role_assignments_are_checked_for_plausibility() -> None:
    """Scenario: SCN-ACT-005"""
    temperature = EntityFacts(state="24.4", unit="°C", device_class="temperature")
    percent = EntityFacts(state="24", unit="%")
    assert check_role(Role.VALVE_READ, temperature) == "role_needs_percent"
    assert check_role(Role.VALVE_READ, percent) is None
    assert check_role(Role.EXTERNAL_TEMPERATURE, percent) == "role_needs_temperature"
    assert check_role(Role.EXTERNAL_TEMPERATURE, temperature) is None
    assert check_role(Role.CHILD_LOCK, temperature) is None


def test_bosch_profile_asks_for_valve_confirmation() -> None:
    """Scenario: SCN-ACT-006"""
    bosch = find_profile(PROFILES, "Bosch", "BTH-RA")
    sonoff = find_profile(PROFILES, "SONOFF", "TRVZB")

    assert bosch.valve_refresh == timedelta(minutes=10)
    assert sonoff.valve_refresh is None


def test_valve_position_is_derived_from_the_device_decision() -> None:
    """Scenario: SCN-ACT-007"""

    def derived(action: str | None) -> float | None:
        return derived_valve_pct(43.0, 70.0, closing_inverted=True, hvac_action=action)

    assert derived("heating") == 43.0
    assert derived("idle") == 30.0
    assert derived("off") == 30.0
    assert derived(None) is None
    assert derived_valve_pct(43.0, 30.0, closing_inverted=False, hvac_action="idle") == 30.0

    sonoff = {Role.CLIMATE: "c", Role.VALVE_WRITE: "w", Role.VALVE_MIN: "m"}
    assert derives_valve(sonoff)
    assert not derives_valve({**sonoff, Role.VALVE_READ: "r"})
    assert not derives_valve({Role.CLIMATE: "c", Role.VALVE_WRITE: "w"})
