# SCN-LRN-002: The learned demand is a robust median, by day and night if needed

**Spec:** LRN-032, LRN-033
**Test:** `tests/core/test_learning.py::test_learned_demand_from_observations`

## Initial state
Observations of quiet hours.

## Steps
1. 20 hours on 4 days.
2. 30 hours on 4 days around 50 %, two outliers at 300 %.
3. A room that would need 10 %.
4. 15 night hours at 40 % and 15 day hours at 80 %; then both at 50 % and 55 %.
5. Observations older than 21 days.

## Expected result
1. `learning`, no factor.
2. `settled`, factor 50 %; the outliers do not move it.
3. Factor limited to 25 %.
4. Night 40 % and day 80 % used separately; with 50/55 % one factor for both.
5. Not counted.

## Why it matters
A bedroom with sleeping people needs less at night than in the day; single disturbed hours
must not change what the controller does.
