# SCN-HEATER-007: Implausible heater entries are rejected at the field

**Spec:** ACT-060, ACT-062, ACT-067
**Test:** `tests/core/test_heater.py::test_heater_entries_are_checked`

## Initial state
The heater dialog.

## Steps
1. Enter 2 stages with outputs 1300 and 1700 W, 40 W while off, a stage sensor.
2. Enter 2 stages with only one output.
3. Enter 2 stages with 1700 and 1300 W.
4. Enter 2 stages with neither stage sensor nor stage setter.
5. Enter exponent 3.
6. Enter 6 stages.

## Expected result
1. Accepted.
2. `heater_outputs_count`.
3. `heater_outputs_rising`.
4. `heater_needs_stage_entity`.
5. `heater_exponent_range`.
6. `heater_stages_range`.

## Why it matters
Wrong outputs would make Thermogeist plan with heat that does not exist; the explanation sits
where the mistake is.
