# Home Assistant integration

How Thermogeist appears in Home Assistant. The HA layer is thin: it collects input, creates
entities and forwards everything to the core (ARC-001).

## Setup

| ID | Requirement | Status |
|---|---|---|
| HAI-001 | Setup through the UI (config flow). No YAML needed. | implemented |
| HAI-002 | One config entry per house; several houses per HA installation are allowed. Step 1 asks only what is required: name, heating type, outdoor temperature sensor. Step 2 (optional details): heat load, design outdoor temperature, share outside Thermogeist, heated living area. | implemented |
| HAI-003 | Every setting can be changed later through the options flow, without removing the integration. | implemented |
| HAI-004 | The house appears as a device. Entities: `select` central mode; diagnostic sensors heating type, heat load, design outdoor temperature, share outside Thermogeist, and the profile defaults (minimum opening, dead band, max. change, max. setback). | implemented |
| HAI-005 | Rooms are config sub-entries of the house. Each room appears as its own device, linked to its HA area. | planned |
| HAI-006 | Thermostats are assigned to a room by picking their HA device. Thermogeist detects the device type and shows the detected capabilities before saving. | planned |

## Conventions

| ID | Requirement | Status |
|---|---|---|
| HAI-010 | All entity names and texts come from `translations/en.json` and `de.json`. | implemented |
| HAI-011 | Entities use `has_entity_name` and stable unique IDs based on the config entry and sub-entry IDs. | implemented |
| HAI-012 | Minimum Home Assistant version: 2026.10.0 (as in `hacs.json`), Python 3.14. | implemented |
