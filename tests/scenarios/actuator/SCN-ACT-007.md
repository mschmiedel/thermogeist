# SCN-ACT-007: Valve position derived from opening and closing positions

**Spec:** ACT-016
**Test:** `tests/core/test_actuator.py::test_valve_position_is_derived_from_the_device_decision`

## Initial state
A Sonoff TRVZB: opening degree 43 %, closing degree 70 % (inverted: 30 % open), no reported
valve position.

## Steps
1. The device reports `hvac_action` heating, idle, off and nothing.
2. A device that reports its valve, and one without a closing position.

## Expected result
1. 43 %, 30 %, 30 %, unknown.
2. Neither derives its position.

## Why it matters
The Sonoff moves between two positions with its own controller; Thermogeist's opening degree
alone does not say where the valve is.
