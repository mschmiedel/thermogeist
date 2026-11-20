# SCN-CONTROL-002: Control writes after the start-up hold

**Spec:** ACT-041, ACT-042, ACT-045
**Test:** `tests/ha/test_control.py::test_control_writes_after_startup_hold`

## Initial state
As SCN-CONTROL-001; room at 19.5 °C, device setpoint 20 °C.

## Steps
1. Switch control on.
2. Wait 91 s.

## Expected result
- 1: reason `startup_hold`, nothing written yet.
- 2: `operating_mode` → manual, `pi_heating_demand` → planned position, `remote_temperature` → 19.5; setpoint not written (already 20 °C).

## Why it matters
Devices get time after a restart; then exactly the needed values are written, nothing more.
