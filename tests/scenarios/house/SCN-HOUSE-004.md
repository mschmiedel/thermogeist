# SCN-HOUSE-004: Each heating type brings its own profile defaults

**Spec:** CTL-013
**Test:** `tests/core/test_profiles.py::test_profile_defaults_per_heating_type`

## Initial state
None.

## Steps
1. Ask for the profile of each heating type.

## Expected result
| | heat pump | boiler | direct electric |
|---|---|---|---|
| minimum opening | 40 % | 0 % | 0 % |
| dead band | 0.5 K | 0.2 K | 0.2 K |
| max. change per 30 min | 10 % | 30 % | 100 % |
| max. setback | 2 K | 4 K | 4 K |

## Why it matters
The heating type is the single most important answer: it decides how calm Thermogeist regulates.
