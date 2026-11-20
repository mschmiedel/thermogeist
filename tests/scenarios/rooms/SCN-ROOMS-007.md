# SCN-ROOMS-007: An unchanged reason is not written again

**Spec:** RSN-002
**Test:** `tests/ha/test_rooms.py::test_reason_is_not_rewritten_while_unchanged`

## Initial state
A room holding its setpoint.

## Steps
1. Let three minutes pass.

## Expected result
- No new state for the active reason; `since` keeps the time the reason started.

## Why it matters
Seen in the field: the reason was stored several times per minute, filling the database.
