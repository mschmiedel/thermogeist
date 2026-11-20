# SCN-THERMO-008: A thermostat can be changed later

**Spec:** HAI-006
**Test:** `tests/ha/test_thermostats.py::test_reconfigure_thermostat`

## Initial state
A Sonoff thermostat assigned with 2000 W.

## Steps
1. Reconfigure: same room and device, 1500 W.
2. Keep the roles.

## Expected result
- The roles are pre-filled with the stored ones.
- The thermostat now shows 1500 W.

## Why it matters
Typos and later knowledge (type plate found) can be corrected without starting over.
