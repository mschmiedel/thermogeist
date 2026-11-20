# SCN-HOUSE-005: A house name made only of spaces is rejected

**Spec:** HAI-002
**Test:** `tests/core/test_house.py::test_blank_name_is_rejected`

## Initial state
A minimal house as in SCN-HOUSE-001, but named "   ".

## Steps
1. Validate the house.

## Expected result
- One issue `name_empty` on the field `name`.

## Why it matters
The name becomes the device name in Home Assistant; an empty one would be confusing.
