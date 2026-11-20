# Operation and overrides

## On-device operation

| ID | Requirement | Status |
|---|---|---|
| OVR-001 | Setpoint changes on the device are detected: via `setpoint_change_source` where available, otherwise by comparing with the last written value. | planned |
| OVR-002 | Debounce: the final value counts only after 20 s without further change. | planned |
| OVR-003 | The value becomes the new room setpoint as an override, with reason code and visible remaining time. | planned |
| OVR-004 | The device display always shows the real room setpoint, never an artificial offset. | planned |

## Override duration

| ID | Requirement | Status |
|---|---|---|
| OVR-010 | Configurable at house level, overridable per room: until the next schedule change (default) / for X hours / permanently. | planned |
| OVR-011 | Changes from the HA UI and from voice assistants use the same mechanism, with their own source. | planned |
| OVR-012 | Each room exposes one `climate` entity with the room setpoint and the room temperature. This is the entity users and voice assistants operate. | planned |

## Device functions

| ID | Requirement | Status |
|---|---|---|
| OVR-020 | Child lock configurable per room and inheritable via groups. | planned |
| OVR-021 | Built-in schedules and built-in window detection on the devices are switched off so there is only one logic. | planned |
