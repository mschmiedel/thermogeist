# Credits

This project stands on the shoulders of others. Whenever an idea, algorithm or piece of code is
taken from or closely inspired by another project, it is listed here.

| Project | License | What we use | Where |
|---|---|---|---|
| [Zigbee2MQTT](https://www.zigbee2mqtt.io/) device documentation, generated from [zigbee-herdsman-converters](https://github.com/Koenkk/zigbee-herdsman-converters) | zigbee-herdsman-converters: MIT; Zigbee2MQTT and its docs: GPL-3.0 (only facts used, no code or text copied) | Expose names, value ranges, firmware requirements and device behaviour of supported thermostats (e.g. Sonoff TRVZB `valve_opening_degree` from firmware 1.1.4, `temperature_accuracy` −1 to −0.2 from 1.3.0, `smart_temperature_control` disabling manual valve positions; Bosch BTH-RA `remote_temperature` expiring after 30 min); the `zigbee2mqtt/bridge/devices` format and the `<ieee>_<expose>_zigbee2mqtt` unique ids of Home Assistant discovery | `custom_components/thermogeist/device_profiles/`, `core/actuator.py` (role resolution), `spec/actuators.md` |

Candidates under consideration:

- [Versatile Thermostat](https://github.com/jmcollin78/versatile_thermostat) (MIT): the TPI
  approach (time-proportional control with indoor and outdoor coefficients) is a likely starting
  point for the "switching" profile. Will be credited here once used.
