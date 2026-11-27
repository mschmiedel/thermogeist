# SCN-FW-001: Firmware versions are compared as dotted numbers

**Spec:** ACT-017
**Test:** `tests/core/test_firmware.py::test_versions_compare_as_dotted_numbers`

## Initial state
A profile that names 1.3.0 as its minimum firmware.

## Steps
Compare installed versions with the minimum.

## Expected result
- 1.1.4 and 1.2.9 are too old; 1.3.0, 1.3, 1.10.0 and "V1.3.1 (build 7)" are not.
- A missing version, a version without a number, or a profile without a minimum never counts as
  too old.

## Why it matters
Firmware texts differ between bridges. A version that cannot be read must not produce a warning
that the user cannot get rid of.
