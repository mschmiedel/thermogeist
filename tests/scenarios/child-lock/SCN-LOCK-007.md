# SCN-LOCK-007: The room switch keeps the lock on

**Spec:** OVR-022
**Test:** `tests/ha/test_child_lock.py::test_room_switch_keeps_the_lock_on`

## Initial state
Room in observe mode with a Sonoff TRVZB, its child lock off.

## Steps
1. Switch *Child lock* of the room on.
2. The device reports its lock off (firmware update).
3. Switch *Child lock* of the room off.

## Expected result
- 1. locks the device; *Child lock: off for 30 min* is unavailable before that.
- 2. locks it again at once, with a logbook entry naming the thermostat.
- 3. unlocks the device.

## Why it matters
The lock works without control mode and survives what resets the device.
