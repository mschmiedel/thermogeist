# SCN-THERMO-019: The written valve cannot be read back as position

**Spec:** ACT-036
**Test:** `tests/ha/test_thermostats.py::test_written_valve_is_no_read_position`

## Initial state
A Sonoff TRVZB being assigned.

## Steps
1. Choose `valve_opening_degree` both as valve position (set) and (read).

## Expected result
- The dialog stays open with an explanation at *Valve position (read)*.

## Why it matters
The written value only echoes Thermogeist; taken as position it started PyM's controller at
100 %.
