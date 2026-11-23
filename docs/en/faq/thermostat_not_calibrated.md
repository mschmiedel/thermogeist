# Thermostat not calibrated

**English** | [Deutsch](../../de/faq/thermostat_not_calibrated.md)

## What you see

A repair issue **… is not calibrated**, and the thermostat's valve position shows *unknown*.

## What it means

The thermostat itself reports that it has lost its calibration: it no longer knows where its valve is open or closed. This happens e.g. after a firmware update. It then stops moving its valve – usually it stays fully open, in the mounting position – but it still accepts every value Thermogeist writes and reports it back. That is why Thermogeist shows the valve position as unknown instead of a wrong number.

Thermogeist only reports it when it lasts 10 minutes: a normal calibration after mounting passes through the same values within about a minute.

## What to do

- **Sonoff TRVZB:** press the button on the thermostat briefly; it calibrates again. Is the child lock on? First press **Child lock: off for 30 min** for the room.
- **Bosch Radiator Thermostat II:** start the calibration in Zigbee2MQTT or on the device, as the manual describes.

The issue disappears by itself as soon as the thermostat reports that it is calibrated again.
