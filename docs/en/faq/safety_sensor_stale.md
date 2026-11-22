# Temperature sensor silent

**English** | [Deutsch](../../de/faq/safety_sensor_stale.md)

## What you see

Active reason: **Temperature sensor silent** (attributes `cause`, `unavailable_minutes` or `silent_minutes`, `limit_minutes`)

## What it means

Thermogeist no longer trusts the room's temperature, for one of two reasons:

- `cause: unavailable` – Home Assistant has shown the sensor as *unavailable* for 15 minutes. That is what happens with an empty battery or a lost radio connection.
- `cause: silent` – the sensor is available but has not sent a new value for 6 hours. Many sensors report only when the temperature changes, so a quiet hour or two in a calm night is normal; six hours are not.

The valve then goes to its minimum opening – never fully off without a reason.

## What to check

1. Battery of the sensor empty or low?
2. Is the sensor still connected (Zigbee2MQTT / ZHA shows it as available)?
3. Was the right sensor selected for the room? Open the Thermogeist entry and click the gear icon (⚙) next to the room → **Edit room**.
4. With `cause: silent`: does the sensor show a value that has not changed for hours although the room has? Then it is stuck – restart or re-pair it.

## What to do

- Fix the cause above. As soon as the sensor reports again, the room returns to normal by itself.
