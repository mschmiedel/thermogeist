# SCN-HEAT-006: The factor of a heat source can come from an entity

**Spec:** MDL-048, MDL-049
**Test:** `tests/core/test_heat.py::test_factor_entity_wins_and_is_limited`

## Initial state
A heat source with a fixed factor of 400 % (an air conditioner with a COP of about 4).

## Steps
1. Work out the factor in use without a factor entity, with a factor entity at 420 %, with an
   unavailable factor entity, with a factor entity at 900 % and at −20 %.

## Expected result
- 400 % without an entity and when the entity is unavailable (fallback to the fixed factor).
- 420 % from the entity.
- 900 % is limited to 500 %, −20 % to 0 %.

## Why it matters
A heat pump moves several times its power into the room; the user can describe that with a
fixed value or a template, and a broken template must not make the radiator heat wildly.
