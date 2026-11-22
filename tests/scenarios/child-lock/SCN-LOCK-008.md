# SCN-LOCK-008: Locking at the device switches the room on

**Spec:** OVR-022
**Test:** `tests/ha/test_child_lock.py::test_lock_at_the_device_switches_the_room_on`

## Initial state
Room with a Sonoff TRVZB, room child lock off.

## Steps
1. The device reports its lock on (switched at the device or in Zigbee2MQTT).

## Expected result
- The room child lock is on, nothing is written, a logbook entry names the thermostat.

## Why it matters
Where the lock is switched on makes no difference.
