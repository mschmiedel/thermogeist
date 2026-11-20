# SCN-ROOMS-002: Too high known shares are rejected in the dialog

**Spec:** MDL-021
**Test:** `tests/ha/test_rooms.py::test_known_share_over_total_is_rejected`

## Initial state
House with 10 % outside Thermogeist and a room with known share 60 %.

## Steps
1. Add a second room with known share 35 %.
2. Change it to 30 %.

## Expected result
- 1: error `known_shares_exceed_total` at the share field.
- 2: room created.

## Why it matters
Errors appear where they can be fixed.
