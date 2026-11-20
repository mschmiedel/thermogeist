# SCN-ROOM-003: A known share must be given and within 0–100 %

**Spec:** MDL-030
**Test:** `tests/core/test_room.py::test_known_share_is_required_and_checked`

## Initial state
A room with share mode known.

## Steps
1. Validate without share.
2. Validate with 120 %.
3. Validate with 14.5 %.

## Expected result
- 1: `known_share_required`.
- 2: `known_share_out_of_range`.
- 3: valid; floor area is not needed.

## Why it matters
People with a heat load calculation should not have to enter geometry.
