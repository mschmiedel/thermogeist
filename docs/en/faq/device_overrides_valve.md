# Thermostat regulates on its own

**English** | [Deutsch](../../de/faq/device_overrides_valve.md)

## What you see

A repair issue **… keeps regulating on its own**, and the room's control switch is off.

## What it means

Thermogeist wrote the valve position several times, but the thermostat changed it back each time – its own regulation is still active. To avoid an endless back and forth, Thermogeist switched control for the room off.

## What to check

1. Bosch Radiator Thermostat II: is `operating_mode` still *manual*? Thermogeist sets it when control starts; a schedule or the Bosch app may change it back.
2. Is a built-in regulation (e.g. Sonoff *smart temperature control*) switched on again?
3. Do automations or other integrations write to the thermostat?

## What to do

- Fix the cause, then switch **Control** on again for the room.
- If it keeps happening, the thermostat cannot be controlled directly – tell us your model, so its profile can be improved.
