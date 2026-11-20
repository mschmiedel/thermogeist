# SCN-CONTROL-007: Rooms with only setpoint-based thermostats cannot be controlled yet

**Spec:** ACT-044
**Test:** `tests/ha/test_control.py::test_setpoint_only_room_cannot_be_controlled`

## Initial state
A room whose only thermostat has no writable valve.

## Steps
1. Switch control on.

## Expected result
- An error explains why; the switch stays off.

## Why it matters
No silent half-control.
