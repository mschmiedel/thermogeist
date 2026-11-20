# SCN-HOUSE-006: Own control values override the profile until reset

**Spec:** CTL-014
**Test:** `tests/core/test_profiles.py::test_overrides_win_and_survive_heating_type_change`

## Initial state
Heat pump house, no own values.

## Steps
1. Set the minimum opening to 30 %.
2. Change the heating type to boiler.
3. Reset (remove all own values).

## Expected result
- After 1: minimum opening 30 % from `user`; dead band 0.5 K from `profile`.
- After 2: minimum opening still 30 % from `user`; dead band 0.2 K from `profile` (boiler).
- After 3: minimum opening 0 % from `profile` (boiler).

## Why it matters
Users can fine-tune without losing the sensible defaults, and always see which values they changed.
