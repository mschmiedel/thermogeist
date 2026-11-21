# SCN-ACT-008: The hardware key follows devices and wiring

**Spec:** CTL-045
**Test:** `tests/core/test_actuator.py::test_hardware_key_follows_devices_and_roles`

## Initial state
A thermostat with device, roles and strategy.

## Steps
1. Compare the key after changing the rated output, a role, the device, and the order of
   thermostats.

## Expected result
- Rated output and order: same key. Role or device: different key.

## Why it matters
Only a real change of the valves may discard what the controller learned.
