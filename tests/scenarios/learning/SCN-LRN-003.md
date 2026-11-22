# SCN-LRN-003: The feed-forward uses the learned demand

**Spec:** LRN-034, LRN-035, LRN-036
**Test:** `tests/ha/test_learning.py::test_feed_forward_uses_learned_demand`

## Initial state
A room with a thermostat that has collected 30 quiet hours on 4 days at 50 % of the modelled
demand.

## Steps
1. Reload the house (the observations are written and read back).
2. Press "Learning: start again".

## Expected result
1. *Learned demand* shows 50 % (`settled`); the feed-forward is computed with half the modelled
   demand.
2. The room is `learning` again and the feed-forward uses the full modelled demand.

## Why it matters
PyM held its target with about half the heat the model expected; the feed-forward should know.
