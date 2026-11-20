# SCN-THERMO-010: Sensor noise does not recompute the plan

**Spec:** CTL-042
**Test:** `tests/ha/test_control.py::test_plan_is_not_recomputed_on_sensor_noise`

## Initial state
A room with a thermostat; the flow sensor toggles between two values every 5 seconds.

## Steps
1. Ten toggles within 50 seconds.

## Expected result
- The planned valve position is stored at most once.

## Why it matters
Field finding: a flow sensor toggling 32.25/32.5 °C rewrote the plan every few seconds into the database.
