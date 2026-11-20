# SCN-CONTROL-004: A thermostat that keeps regulating on its own is given up on

**Spec:** ACT-043, RSN-004
**Test:** `tests/ha/test_control.py::test_gives_up_when_device_keeps_regulating`

## Initial state
Controlled Bosch; after the first write it keeps reporting 14 %.

## Steps
1. Let 40 minutes pass.

## Expected result
- The same position is written once and rewritten three times.
- Then control switches off, a repair issue appears and the logbook names the thermostat.

## Why it matters
No endless fight with a device – and the user learns why control stopped.
