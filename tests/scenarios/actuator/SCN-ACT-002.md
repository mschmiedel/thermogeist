# SCN-ACT-002: Sonoff roles are found from Zigbee2MQTT entity ids

**Spec:** ACT-001 to ACT-006, ACT-032
**Test:** `tests/core/test_actuator.py::test_sonoff_roles_are_resolved_from_z2m_unique_ids`

## Initial state
A Sonoff TRVZB device with climate, valve opening/closing degree, external temperature, child lock and battery entities.

## Steps
1. Resolve roles with the TRVZB profile.

## Expected result
- Climate by domain, the rest by expose name; battery is ignored.
- The minimum opening is marked inverted (closing degree).
- Kind: valve-based.

## Why it matters
The dialog is pre-filled correctly; users only check it.
