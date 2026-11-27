# SPDX-License-Identifier: MIT
"""Minimum firmware from the device profile (spec ACT-017)."""

from custom_components.thermogeist.core.firmware import firmware_too_old, parse_version


def test_versions_compare_as_dotted_numbers() -> None:
    """Scenario: SCN-FW-001"""
    assert firmware_too_old("1.1.4", "1.3.0")
    assert firmware_too_old("1.2.9", "1.3.0")
    assert not firmware_too_old("1.3.0", "1.3.0")
    assert not firmware_too_old("1.3", "1.3.0")
    assert not firmware_too_old("1.10.0", "1.3.0")
    assert not firmware_too_old("V1.3.1 (build 7)", "1.3.0")
    assert parse_version("V1.3.1 (build 7)") == (1, 3, 1)

    assert not firmware_too_old(None, "1.3.0")
    assert not firmware_too_old("unknown", "1.3.0")
    assert not firmware_too_old("1.1.4", None)
