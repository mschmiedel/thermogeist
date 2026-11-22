# SCN-ACT-009: Roles are derived from Zigbee2MQTT exposes

**Spec:** ACT-037, ACT-038
**Test:** `tests/core/test_exposes.py::test_roles_are_derived_from_exposes`

## Initial state
Expose lists as Zigbee2MQTT publishes them on `bridge/devices` for three kinds of thermostat:
a valve position written as opening degree with a closing degree (as the Sonoff TRVZB), a
settable `pi_heating_demand` (as the Bosch BTH-RA), and a read-only `pi_heating_demand` with
an external sensor without unit (as some Danfoss variants); plus a device that is no thermostat.

## Steps
1. Derive the roles.

## Expected result
- Opening degree → `valve_write`, closing degree → `valve_min` (inverted), external
  temperature in °C → `external_temperature`, child lock found inside a composite expose.
- Settable `pi_heating_demand` → `valve_write`, no `valve_read` (the same expose is never read
  back, ACT-036).
- Read-only `pi_heating_demand` → `valve_read` only; the external sensor without °C is ignored;
  the kind stays setpoint-based.
- The non-thermostat gives no profile.

## Why it matters
Hundreds of thermostats work with Zigbee2MQTT; the common expose names cover most of them
without a profile file per model.
