# SCN-SETUP-004: The central mode survives a restart

**Spec:** RUL-003
**Test:** `tests/ha/test_select.py::test_central_mode_is_restored`

## Initial state
A house whose central mode was set to `frost_protection` before Home Assistant stopped.

## Steps
1. Start Home Assistant again.

## Expected result
- The central mode is still `frost_protection`.

## Why it matters
A house set to frost protection for the holidays must not silently start heating after a power cut.
