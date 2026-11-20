# SCN-CONTROL-005: Turning the knob sets the room setpoint

**Spec:** OVR-001, OVR-002, RSN-003
**Test:** `tests/ha/test_control.py::test_setpoint_on_device_becomes_room_setpoint`

## Initial state
Controlled Bosch, room setpoint 20 °C.

## Steps
1. Device setpoint changes to 22 °C.
2. After 10 s.
3. After 21 s.

## Expected result
- 2: room still 20 °C (debounce).
- 3: room setpoint 22 °C, logbook entry.

## Why it matters
The thermostat stays usable by hand; its knob simply changes the room.
