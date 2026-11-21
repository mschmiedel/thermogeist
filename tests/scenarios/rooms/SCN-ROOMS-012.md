# SCN-ROOMS-012: An air conditioner heats the room with its COP from a template

**Spec:** MDL-048, MDL-049, MDL-044
**Test:** `tests/ha/test_heat_sources.py::test_factor_entity_sets_heat_from_devices`

## Initial state
A room dialog with an air conditioner drawing 500 W as heat source.

## Steps
1. In the factor step enter 400 % and choose a factor sensor that reads 420 %.
2. The factor sensor becomes unavailable; one minute passes.

## Expected result
- The room stores `factor: 400` and `factor_entity` for the source.
- "Heat from devices" shows 2100 W (500 W × 420 %); attribute `sources` shows 420.
- With the sensor unavailable: 2000 W from the fixed 400 %.

## Why it matters
The template follows the outdoor temperature; the fixed factor keeps the room sensible when the
template breaks.
