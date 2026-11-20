# SCN-CTL-006: Central stop closes, a silent sensor goes to a safe opening

**Spec:** CTL-034
**Test:** `tests/core/test_controller.py::test_stop_and_safety_override_regulation`

## Initial state
Heat-pump profile.

## Steps
1. Step without target.
2. Step with safety flag.
3. Safety with the boiler profile.

## Expected result
- 1: 0 %, limit `stopped`.
- 2: 40 % (minimum opening), limit `safety`.
- 3: 20 % (never below 20 % in safety).

## Why it matters
A broken sensor never leads to a closed valve and a cold room.
