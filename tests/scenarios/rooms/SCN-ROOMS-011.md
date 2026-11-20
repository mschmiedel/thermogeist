# SCN-ROOMS-011: Frost guard with an open window, end to end

**Spec:** RUL-015
**Test:** `tests/ha/test_windows.py::test_frost_guard_with_open_window`

## Initial state
A room with an open window (31 s), room at 19.5 °C.

## Steps
1. The room cools to 6.5 °C; one minute passes.

## Expected result
- Reason stays `window_open` with `frost_guard: on`; the window sensor shows `frost_guard: true`.
- A logbook entry explains that the room is heated to frost protection.

## Why it matters
Users see why the radiator heats although the window is open.
