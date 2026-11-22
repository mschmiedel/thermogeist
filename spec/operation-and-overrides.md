# Operation and overrides

## On-device operation

| ID | Requirement | Status |
|---|---|---|
| OVR-001 | In control mode, setpoint changes on a **valve-based** thermostat are detected by comparing with the last value Thermogeist wrote. The new value becomes the room setpoint until further notice (no schedules yet) and is written to the logbook. In observe mode the device is left alone. | implemented |
| OVR-002 | Debounce: the final value counts only after 20 s without further change. | implemented |
| OVR-003 | The value becomes the new room setpoint as an override, with reason code and visible remaining time. | planned |
| OVR-004 | A valve-based thermostat's display shows the real room setpoint. With the setpoint strategy (ACT-050) everything the thermostat shows or reports as its setpoint is ignored, with or without external temperature input: Thermogeist cannot tell a turned knob from the device's own schedule, window or frost function, and later schedules in Thermogeist need one clear source of truth. A changed device setpoint is never adopted; Thermogeist writes its own value back at the next apply (after the window grace period of OVR-005, so it does not fight the device's window function). The room setpoint is set in Home Assistant only. | implemented |
| OVR-005 | For valve-based thermostats (setpoint thermostats see OVR-004): while a window contact of the room is open, and for 2 minutes after all are closed again (`WINDOW_DEVICE_GRACE`), a changed device setpoint is not adopted: it is most likely the device's own window function (e.g. Bosch Room Climate Control lowers to 8 °C and restores its value on closing), which Thermogeist cannot tell apart from a turned knob. Afterwards Thermogeist writes its own value again if the device still shows something else. The ignored change appears only in the debug log. Rooms without window contacts in Thermogeist are not covered. | implemented |
| OVR-006 | The user docs mark the limits of the setpoint strategy prominently: the thermostat's display and knob are ignored (OVR-004), the display may show a corrected value (ACT-052), and the device's own controller decides how far the valve opens, so uneven behaviour (e.g. overheating by half a degree) is always possible. Valve control is preferred where the device offers it; the device's own schedules and window detection should be switched off. | implemented |

## Override duration

| ID | Requirement | Status |
|---|---|---|
| OVR-010 | Configurable at house level, overridable per room: until the next schedule change (default) / for X hours / permanently. | planned |
| OVR-011 | Changes from the HA UI and from voice assistants use the same mechanism, with their own source. | implemented |
| OVR-012 | Each room exposes one `climate` entity with the room setpoint (5–30 °C, step 0.5, default 20 °C) and the room temperature. This is the entity users and voice assistants operate. The setpoint survives restarts. | implemented |

## Device functions

| ID | Requirement | Status |
|---|---|---|
| OVR-020 | Child lock inheritable via groups (per room: OVR-022). | planned |
| OVR-021 | Built-in schedules and built-in window detection on the devices are switched off so there is only one logic. | planned |
| OVR-022 | **Smart child lock.** Rooms with at least one thermostat with the `child_lock` role (switch, lock or select with lock/unlock options) get a switch *Child lock*. It works in observe and control mode: it is an explicit wish, not a control decision. On locks all those thermostats of the room, off unlocks them. A device that is locked by someone (at the device, in Zigbee2MQTT) while the switch is off switches the room on, and the other thermostats of the room follow. A device whose lock goes off while the switch is on is locked again at once (firmware update, battery change, someone at the device: Thermogeist cannot tell them apart, so the switch is the only way to switch the lock off for good). Coming back from unavailable is no change. Without news, a device that still shows unlocked gets the lock again at most every 10 minutes (`CHILD_LOCK_RETRY_AFTER`, as ACT-049), to spare its battery. Adopting and setting again write a logbook entry naming the thermostat. Setpoint-strategy thermostats from other integrations (e.g. Bosch Smart Home) take part only if a `child_lock` entity is assigned. | implemented |
| OVR-023 | **Unlock for a while.** Per room a button *Child lock: off for 30 min*, available while the child lock is on: all thermostats of the room are unlocked and a logbook entry says until when. The switch shows what applies right now: off during the 30 minutes; switching it on ends them and locks at once, switching it off keeps the lock off for good. A timestamp sensor *Child lock back on* shows when the lock returns (Home Assistant displays it as "in 27 minutes"), unknown outside the 30 minutes. After 30 minutes (`CHILD_LOCK_UNLOCK`, checked every minute) the lock goes on again by itself, also across a restart (stored end time), with a logbook entry. Locking a device in between ends the time early. The time is fixed: one less setting. Calibration stays separate (CAL-003). | implemented |
| OVR-024 | A room seen for the first time (no stored wish) takes over what its devices show as soon as one reports: on if any is locked. Adding Thermogeist never switches a lock off. | implemented |
