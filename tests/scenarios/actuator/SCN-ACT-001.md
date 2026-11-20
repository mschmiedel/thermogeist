# SCN-ACT-001: Known thermostats are recognised by manufacturer and model id

**Spec:** ACT-030, ACT-031
**Test:** `tests/core/test_actuator.py::test_profiles_match_by_manufacturer_and_model_id`

## Initial state
The three shipped profiles.

## Steps
1. Look up SONOFF/TRVZB, Bosch/bth-ra, Acme/TRVZB and SONOFF without model id.

## Expected result
- Sonoff and Bosch are found (case does not matter).
- Wrong manufacturer or missing model id: no profile.

## Why it matters
Assigning a known thermostat needs no manual setup.
