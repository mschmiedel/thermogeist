# SCN-ROOMS-010: A room overrides the house window delay

**Spec:** RUL-014
**Test:** `tests/ha/test_windows.py::test_room_overrides_house_window_delay`

## Initial state
A room with one window contact; house defaults 30 s / 10 s.

## Steps
1. Read the house and room entities.
2. Set the room's *close after* to 5 s; open the window for 6 s.
3. Press *Window: reset times to house*.

## Expected result
- Room shows 30 s and 10 s with `source: house`.
- After the change `source: room`; after 6 s the room is `window_open`. The room's window sensor
  is on, lists the contact, `heating_paused: true`, `close_after_s: 5`.
- After the reset: 30 s, `source: house`.

## Why it matters
Windows behave per room as the user wants, and the current state is visible on the room.
