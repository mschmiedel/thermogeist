# SCN-SHARE-002: High ceilings and exposed rooms weigh more, sloped rooms less

**Spec:** MDL-033, MDL-034
**Test:** `tests/core/test_estimation.py::test_height_and_exposure_change_the_weight`

## Initial state
House with 160 m² living area.

## Steps
1. Living room 40 m², 3.5 m high, three exterior walls, ground below.
2. Attic room 15 m², 2.8 m highest and 1.2 m lowest point, two exterior walls, roof above.

## Expected result
- Living room: height factor 1.225, exposure 1.3 → 39.81 %.
- Attic room: height factor 0.9, exposure 1.3 → 10.97 %.

## Why it matters
The cases from the planning discussion (gallery living room, attic with slope) are handled explicitly.
