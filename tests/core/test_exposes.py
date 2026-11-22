# SPDX-License-Identifier: MIT
"""Roles from Zigbee2MQTT exposes (spec ACT-034, ACT-037, ACT-038)."""

from custom_components.thermogeist.core.actuator import Kind, Role, Source
from custom_components.thermogeist.core.exposes import (
    AUTO_PROFILE_ID,
    profile_from_exposes,
    roles_from_exposes,
)

ALL = 7  # published, settable, gettable
READ = 5  # published, gettable

CLIMATE = {
    "type": "climate",
    "features": [
        {"type": "numeric", "name": "occupied_heating_setpoint", "access": ALL, "unit": "°C"},
        {"type": "numeric", "name": "local_temperature", "access": READ, "unit": "°C"},
    ],
}


def numeric(name: str, access: int, unit: str | None) -> dict[str, object]:
    expose: dict[str, object] = {"type": "numeric", "name": name, "property": name}
    expose["access"] = access
    if unit is not None:
        expose["unit"] = unit
    return expose


def test_roles_are_derived_from_exposes() -> None:
    """Scenario: SCN-ACT-009"""
    opening_degree = [
        CLIMATE,
        numeric("valve_opening_degree", ALL, "%"),
        numeric("valve_closing_degree", ALL, "%"),
        numeric("external_temperature_input", ALL, "°C"),
        {
            "type": "composite",
            "features": [{"type": "binary", "name": "child_lock", "access": ALL}],
        },
    ]
    roles = roles_from_exposes(opening_degree)
    assert roles[Role.VALVE_WRITE].expose == "valve_opening_degree"
    assert roles[Role.VALVE_MIN].expose == "valve_closing_degree"
    assert roles[Role.VALVE_MIN].inverted
    assert roles[Role.EXTERNAL_TEMPERATURE].expose == "external_temperature_input"
    assert roles[Role.CHILD_LOCK].expose == "child_lock"
    profile = profile_from_exposes(opening_degree, "auto")
    assert profile is not None
    assert profile.profile_id == AUTO_PROFILE_ID
    assert profile.kind is Kind.VALVE
    assert profile.control_settings == {}
    assert profile.roles[Source.Z2M] == roles

    settable_demand = [CLIMATE, numeric("pi_heating_demand", ALL, "%")]
    roles = roles_from_exposes(settable_demand)
    assert roles[Role.VALVE_WRITE].expose == "pi_heating_demand"
    assert Role.VALVE_READ not in roles

    reported_demand = [
        CLIMATE,
        numeric("pi_heating_demand", READ, "%"),
        numeric("external_measured_room_sensor", ALL, None),
    ]
    roles = roles_from_exposes(reported_demand)
    assert roles == {Role.VALVE_READ: roles[Role.VALVE_READ]}
    assert roles[Role.VALVE_READ].expose == "pi_heating_demand"
    reported = profile_from_exposes(reported_demand, "auto")
    assert reported is not None
    assert reported.kind is Kind.SETPOINT

    assert profile_from_exposes([numeric("brightness", ALL, None)], "auto") is None
