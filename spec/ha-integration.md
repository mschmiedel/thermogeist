# Home Assistant integration

How Thermogeist appears in Home Assistant. The HA layer is thin: it collects input, creates
entities and forwards everything to the core (ARC-001).

## Setup

| ID | Requirement | Status |
|---|---|---|
| HAI-001 | Setup through the UI (config flow). No YAML needed. | implemented |
| HAI-002 | One config entry per house; several houses per HA installation are allowed. Step 1 asks only what is required: name, heating type, outdoor temperature sensor. Step 2 (optional details): heat load, design outdoor temperature, share outside Thermogeist, heated living area. | implemented |
| HAI-003 | Every setting can be changed later through the options flow, without removing the integration. | implemented |
| HAI-004 | The house appears as a device. Entities: `select` central mode; editable control settings (CTL-014) with a reset button; diagnostic sensors heating type, heat load, design outdoor temperature, share outside Thermogeist, heat load not assigned to a room. | implemented |
| HAI-005 | Rooms are config sub-entries of the house ("Add room" on the house entry; reconfigure to change). Step 1: name, optional HA area, room temperature sensor, share mode. Step 2: size and position (MDL-033) or known share (MDL-030). Each room is a device below the house device, placed in the chosen area. Entities: `climate` (OVR-012), sensors active reason, target temperature, heat demand, and diagnostic share and heat loss coefficient. | implemented |
| HAI-006 | Thermostats are assigned to a room by picking their HA device. Thermogeist detects the device type and shows the detected capabilities before saving. | planned |

## Conventions

| ID | Requirement | Status |
|---|---|---|
| HAI-010 | All entity names and texts come from `translations/en.json` and `de.json`. | implemented |
| HAI-011 | Entities use `has_entity_name` and stable unique IDs based on the config entry and sub-entry IDs. | implemented |
| HAI-012 | Minimum Home Assistant version: 2026.10.0 (as in `hacs.json`), Python 3.14. | implemented |
| HAI-013 | Every entity has a meaningful icon from `icons.json`, with state-dependent icons for enums. | implemented |
