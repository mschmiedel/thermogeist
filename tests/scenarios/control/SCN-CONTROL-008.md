# SCN-CONTROL-008: The Bosch valve position is confirmed before it times out

**Spec:** ACT-047
**Test:** `tests/ha/test_control.py::test_bosch_valve_is_confirmed_before_it_times_out`

## Initial state
Controlled Bosch BTH-RA, simulated like the real device: it drops an external valve position 15 minutes after the last write.

## Steps
1. Let 60 minutes pass with a steady plan.

## Expected result
- The valve value is resent every 10 minutes (no motor movement, same value).
- The device never drops to 0, control stays on, no repair issue.

## Why it matters
Field finding: the real Bosch fell to 0 % exactly 15:10–15:12 minutes after each write.
