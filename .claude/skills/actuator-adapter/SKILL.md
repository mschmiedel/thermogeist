---
name: actuator-adapter
description: Add or change support for a thermostat/valve device (e.g. Sonoff TRVZB, Bosch BTH-RA, generic climate). Use when a new device type is supported or a device quirk must be handled.
---

# Add or change an actuator adapter

1. **Research the device.** Read its Zigbee2MQTT device page (exposes, access rights, firmware
   notes). Record facts in `spec/actuators.md` under the device, with the source. Mark anything
   unverified as open in `spec/open-questions.md` (device checklist).
2. **Map capabilities.** Fill the capability model (`valve_write`, `valve_read`,
   `valve_min_on_device`, `external_temperature`, `calibration_trigger`, `child_lock`,
   `setpoint_source`). Choose the strategy (direct valve / setpoint modulation /
   time-proportional) from the capabilities, never from the device name.
3. **Preconditions and restore.** If an action needs another setting changed first (e.g. child
   lock off before calibration), declare it as a precondition and restore the original state
   afterwards, including after a restart.
4. **Safe fallback.** Define what the device does if HA stops talking to it (minimum opening on
   the device, own sensor fallback, timeout of external temperature). Document it in the spec and
   in `docs/en/devices.md` + `docs/de/devices.md`.
5. **Device model in the simulator.** Add a simulated device that reproduces the quirks
   (opening point scatter, backlash, ignored writes, report delays) so tests can cover them.
6. **Scenarios.** Use the `test-scenario` skill for: normal control, fallback, firmware too old,
   recalibration detected, manual knob change.
7. **Reason codes.** Device-specific limitations get reason codes with user-facing text.
