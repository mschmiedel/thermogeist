# SCN-SHARE-001: A typical room gets its share of the living area

**Spec:** MDL-031, MDL-034
**Test:** `tests/core/test_estimation.py::test_typical_room_matches_area_share`

## Initial state
House with 160 m² living area. Room 20 m², 2.5 m, two exterior walls, heated above and below.

## Steps
1. Calculate the shares.

## Expected result
- Room share 12.5 %.
- Not assigned 87.5 %.

## Why it matters
The estimate is easy to understand: a normal room counts like its floor area.
