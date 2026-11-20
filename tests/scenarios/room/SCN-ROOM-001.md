# SCN-ROOM-001: A room estimated from size needs only floor area

**Spec:** MDL-033
**Test:** `tests/core/test_room.py::test_estimated_room_needs_floor_area`

## Initial state
A room "Office" with a temperature sensor, share mode estimated.

## Steps
1. Validate without floor area.
2. Validate with 12 m².

## Expected result
- Step 1: one issue `floor_area_required`.
- Step 2: valid, with defaults 2.5 m height and one exterior wall.

## Why it matters
The room dialog asks little; the defaults cover the common case.
