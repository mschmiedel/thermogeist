# SCN-ROOM-002: Sloped ceilings use the mean height

**Spec:** MDL-033
**Test:** `tests/core/test_room.py::test_sloped_ceiling_uses_mean_height`

## Initial state
An attic room with highest point 2.8 m.

## Steps
1. Set the lowest point to 1.2 m.
2. Set the lowest point to 3.0 m.

## Expected result
- Step 1: mean height 2.0 m, valid.
- Step 2: issue `ceiling_low_above_height`.

## Why it matters
Attic rooms are common; a typo like swapping lowest and highest point is caught.
