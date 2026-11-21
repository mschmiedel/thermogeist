# SCN-THERMO-018: Stale entities are removed after setup

**Spec:** HAI-017
**Test:** `tests/ha/test_thermostats.py::test_stale_entities_are_removed`

## Initial state
A house with a room and a thermostat. The entity registry still holds an entity of this house
that the current configuration no longer creates (e.g. the valve position of a thermostat that
was edited and can no longer read its valve).

## Steps
1. Reload the house.

## Expected result
- The stale entity is gone; all entities the configuration creates remain.

## Why it matters
An entity that stays "unavailable" forever looks like a fault.
