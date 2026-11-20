# Window open

**English** | [Deutsch](../../de/faq/window_open.md)

## What you see

Active reason: **Window open** (attributes `open_minutes`, and `frost_guard` while the frost
guard heats). The room's **Windows** sensor shows the contacts and whether heating is paused.

## What it means

A window or door contact of the room has been open for at least *Window: close after* (default
30 seconds). The room aims for frost protection (7 °C) and, if controlled, closes the valve at
once; setpoint thermostats get 5 °C.

**Frost guard:** if the room falls below 7 °C although the window is open, Thermogeist heats it
back to 7 °C (attribute `frost_guard: on`, logbook entry). Above 8 °C the valve closes again.

## What to check

1. Is a window or door really open?
2. Does the contact report correctly (battery, position of the magnet)?

## What to do

- Close the window. After *Window: resume heating after* (default 10 seconds) the room returns to
  its setpoint, with the valve where it was before. The delay bridges switching from fully open
  to tilted.
- Change the times on the house (**Configuration** section of the house device) or per room
  (**Configuration** section of the room device). *Window: reset times to house* on the room
  makes it follow the house again.
