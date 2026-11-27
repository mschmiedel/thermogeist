# Thermostat firmware too old

**English** | [Deutsch](../../de/faq/thermostat_firmware_old.md)

## What you see

A repair issue **…: please update the firmware**, naming the installed and the required version.

## What it means

The thermostat's profile names the oldest firmware with which everything Thermogeist uses works.
Your thermostat reports an older one. Thermogeist keeps controlling it, but some features may be
missing. Example Sonoff TRVZB: before 1.3.0 it lacks *temperature accuracy* and starts heating
only 1 K below its setpoint, so the room stays a little too cold; before 1.1.4 it cannot take a
valve position at all.

Thermogeist reads the version Home Assistant shows for the device (*Settings → Devices*).

## What to do

Update the thermostat's firmware through your Zigbee bridge (Zigbee2MQTT: *OTA* tab). The issue
disappears by itself as soon as the thermostat reports the newer version.
