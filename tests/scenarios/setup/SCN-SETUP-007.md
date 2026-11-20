# SCN-SETUP-007: Reset brings back the profile values

**Spec:** CTL-014
**Test:** `tests/ha/test_controls.py::test_reset_restores_profile`

## Initial state
Heat pump house with minimum opening set to 30 %.

## Steps
1. Press "Reset control settings to profile".

## Expected result
- Minimum opening 40 %, attribute `source` = `profile`.

## Why it matters
Experiments can always be undone with one press.
