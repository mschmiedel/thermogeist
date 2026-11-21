# SCN-CTL-022: A restart continues from the last plan

**Spec:** CTL-040, CTL-034
**Test:** `tests/core/test_controller.py::test_restart_continues_from_the_last_plan`

## Initial state
A controller planning about 46 %, its state saved.

## Steps
1. Restart: restore the saved state; the first step has no room temperature yet.
2. One minute later the room temperature is there; the flow is low, so the feed-forward alone
   asks for 100 %.

## Expected result
1. The last plan is kept (not the safe position).
2. The plan continues from there, rate-limited – no jump to 100 %.

## Why it matters
After restarts every room jumped from 30–50 % to 100 % (or to the safe 30 %) and crept from
there, although nothing in the house had changed.
