# Heater does not run

**English** | [Deutsch](../../de/faq/heater_not_running.md)

## What you see

The binary sensor ***heater* not running** is on, a repair issue **… does not run** appears, and
the logbook says the heater is switched on but does not run.

## What it means

The heater's switch is on, but its stage sensor has reported `0` for 3 minutes in a row. A few seconds at `0` – e.g. while you change the stage on the device – do not count. Heat
Thermogeist expects does not reach the room, so while this lasts it counts no heat from this
heater. The problem clears by itself as soon as the stage sensor reports a stage again.

## What to check

- Is the heater itself switched on (its own switch or thermostat) and the fuse in?
- Does the fan run? On a plinth heater with a water thermostat, the fan may wait for warm water.
- Does the stage sensor's template still fit? A smart plug that reports its power less often, or
  limits that no longer match the fan's power, make the template report `0`.

Use the binary sensor in an automation to be notified, e.g. on your phone.
