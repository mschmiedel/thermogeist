# SCN-DEC-009: Frost guard while a window is open

**Spec:** RUL-015
**Test:** `tests/core/test_decisions.py::test_frost_guard_heats_a_cold_room_with_open_window`

## Initial state
A window open for 5 minutes.

## Steps
1. Room at 6.9 °C; then 7.8 °C with the guard active; then 8.1 °C; then 7.5 °C without guard.

## Expected result
- 6.9 °C: `window_open` with `frost_guard: on`, target 7 °C, valve not forced closed.
- 7.8 °C: guard stays on (hysteresis up to 8 °C).
- 8.1 °C: guard off, valve closed again.
- 7.5 °C without previous guard: valve closed.

## Why it matters
A window forgotten open in winter must not let the room freeze.
