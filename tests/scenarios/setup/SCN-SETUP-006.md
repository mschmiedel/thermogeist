# SCN-SETUP-006: Control values can be changed on the house device

**Spec:** CTL-014
**Test:** `tests/ha/test_controls.py::test_override_persists_and_survives_heating_type_change`

## Initial state
Heat pump house.

## Steps
1. Set minimum opening to 30 %.
2. Reload.
3. Change heating type to boiler.

## Expected result
- After 1 and 2: 30 %, attribute `source` = `user`.
- After 3: minimum opening still 30 %, dead band 0.2 K from the boiler profile.

## Why it matters
Tuning is done where the values are shown, and survives restarts.
