# Operation and overrides

## On-device operation

| ID | Requirement | Status |
|---|---|---|
| OVR-001 | In control mode, setpoint changes on the device are detected by comparing with the last value Thermogeist wrote. The new value becomes the room setpoint until further notice (no schedules yet) and is written to the logbook. In observe mode the device is left alone. | implemented |
| OVR-002 | Debounce: the final value counts only after 20 s without further change. | implemented |
| OVR-003 | The value becomes the new room setpoint as an override, with reason code and visible remaining time. | planned |
| OVR-004 | The device display shows the real room setpoint. Exception: a setpoint thermostat without external temperature input shows the corrected setpoint (ACT-052); turning its knob changes the room setpoint by the same difference. | implemented |
| OVR-005 | While a window contact of the room is open, and for 2 minutes after all are closed again (`WINDOW_DEVICE_GRACE`), a changed device setpoint is not adopted: it is most likely the device's own window function (e.g. Bosch Room Climate Control lowers to 8 °C and restores its value on closing), which Thermogeist cannot tell apart from a turned knob. Afterwards Thermogeist writes its own value again if the device still shows something else. The ignored change appears only in the debug log. Rooms without window contacts in Thermogeist are not covered. | implemented |
| OVR-006 | The user docs state the limits of the setpoint strategy: Thermogeist only sees the device setpoint, not who changed it (a person at the knob, the device's schedule, window or frost function), and the display may show a corrected value (ACT-052). Uneven behaviour is therefore always possible; valve control is preferred where the device offers it. | implemented |

## Override duration

| ID | Requirement | Status |
|---|---|---|
| OVR-010 | Configurable at house level, overridable per room: until the next schedule change (default) / for X hours / permanently. | planned |
| OVR-011 | Changes from the HA UI and from voice assistants use the same mechanism, with their own source. | implemented |
| OVR-012 | Each room exposes one `climate` entity with the room setpoint (5–30 °C, step 0.5, default 20 °C) and the room temperature. This is the entity users and voice assistants operate. The setpoint survives restarts. | implemented |

## Device functions

| ID | Requirement | Status |
|---|---|---|
| OVR-020 | Child lock configurable per room and inheritable via groups. | planned |
| OVR-021 | Built-in schedules and built-in window detection on the devices are switched off so there is only one logic. | planned |
