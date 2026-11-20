# Temperature sensor silent

**English** | [Deutsch](../../de/faq/safety_sensor_stale.md)

## What you see

Active reason: **Temperature sensor silent** (attributes `silent_minutes`, `limit_minutes`)

## What it means

The room's temperature sensor has not sent a valid value for 60 minutes. Thermogeist does not trust old values, so it marks the room. From the version that controls thermostats, the valve then goes to its minimum opening – never fully off without a reason.

## What to check

1. Battery of the sensor empty or low?
2. Is the sensor still connected (Zigbee2MQTT / ZHA shows it as available)?
3. Was the right sensor selected for the room? Open the room and choose **Reconfigure**.
4. Some sensors only report when the temperature changes. If yours stays silent for more than an hour on purpose, tell us – the limit will become configurable.

## What to do

- Fix the cause above. As soon as the sensor reports again, the room returns to normal by itself.
