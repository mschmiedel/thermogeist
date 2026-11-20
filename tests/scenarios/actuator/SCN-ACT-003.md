# SCN-ACT-003: Bosch reads and writes the valve through one entity

**Spec:** ACT-120
**Test:** `tests/core/test_actuator.py::test_bosch_uses_one_entity_to_read_and_write_the_valve`

## Initial state
A Bosch BTH-RA with climate and pi_heating_demand.

## Steps
1. Resolve roles with the BTH-RA profile.

## Expected result
- valve_read and valve_write both point to pi_heating_demand.
- No minimum opening role (the device has none).

## Why it matters
The comparison planned vs. actual works with the thermostats already installed.
