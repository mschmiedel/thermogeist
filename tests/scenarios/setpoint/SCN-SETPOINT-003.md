# SCN-SETPOINT-003: The device setpoint is rounded and kept within 5–30 °C

**Spec:** ACT-052
**Test:** `tests/core/test_setpoint.py::test_setpoint_is_rounded_and_limited`

## Initial state
Extreme offsets and targets.

## Steps
1. Target 28 °C with +7 K offset; target 7 °C with −4 K offset; target 20.2 °C; no target.

## Expected result
- 30 °C, 5 °C, 20 °C, and 5 °C (closed) respectively.

## Why it matters
Devices reject values outside their range; a broken sensor must not send absurd setpoints.
