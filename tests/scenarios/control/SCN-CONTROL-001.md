# SCN-CONTROL-001: Observe mode writes nothing

**Spec:** ACT-014, ACT-040
**Test:** `tests/ha/test_control.py::test_observe_mode_writes_nothing`

## Initial state
A room with a Bosch BTH-RA, control switch off.

## Steps
1. Let three minutes pass.

## Expected result
- No service call to any device.

## Why it matters
Observing is risk-free; the existing regulation stays untouched.
