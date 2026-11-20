# SCN-THERMO-012: The valve strategy needs a writable valve

**Spec:** ACT-050
**Test:** `tests/ha/test_thermostats.py::test_valve_strategy_needs_a_writable_valve`

## Initial state
An unknown thermostat without a valve position entity.

## Steps
1. Choose the strategy *valve* in the dialog.

## Expected result
- The dialog shows an error at the strategy field.

## Why it matters
No strategy that silently cannot work.
