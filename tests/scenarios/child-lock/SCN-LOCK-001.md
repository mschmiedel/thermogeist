# SCN-LOCK-001: A room seen for the first time takes over its devices

**Spec:** OVR-024
**Test:** `tests/core/test_child_lock.py::test_first_seen_takes_over_the_devices`

## Initial state
A room with a child-lock thermostat that Thermogeist has never seen (no stored wish).

## Steps
1. The devices are not available yet.
2. Later one device reports locked, another unlocked.

## Expected result
- While nothing is known, the room switch has no value and nothing is written.
- As soon as a device reports, the switch takes over: on if any device is locked.
- This happens only once; afterwards device changes count as changes.

## Why it matters
Locks that were set before installing Thermogeist are not switched off silently.
