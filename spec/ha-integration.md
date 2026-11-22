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
| HAI-006 | Thermostats belong to a room and are managed in the room's dialog (HAI-007). Step 1: HA device with a climate entity, optional radiator rated output. Step 2: detected profile and kind, every role pre-filled and editable (ACT-030 to ACT-033), strategy and valve confirmation. Entities on the room device: planned valve position (with parts as attributes) per room; actual valve position per thermostat where readable. | implemented |
| HAI-007 | Thermostats belong visibly to their room. Home Assistant shows config sub-entries flat and cannot nest them, so a thermostat sub-entry always appears as its own card next to the room. Instead thermostats become part of the room's sub-entry: (a) "Add room" creates the room as today; (b) the room's gear icon opens a menu: *Edit room*, *Add thermostat*, *Edit thermostat …*, *Remove thermostat …* (the latter two list the room's thermostats); (c) the house-level "Add thermostat" button disappears; (d) moving a thermostat to another room = remove here, add there (its device settings are restored on removal, ACT-008); (e) existing thermostat sub-entries are migrated into their room once (config entry 1.1 → 1.2), keeping roles, strategy, rated output and confirmation interval, and keeping entity unique IDs so history stays; (f) the house device stays under "devices not belonging to a sub-entry" (fixed by Home Assistant). | implemented |

## Conventions

| ID | Requirement | Status |
|---|---|---|
| HAI-010 | All entity names and texts come from `translations/en.json` and `de.json`. | implemented |
| HAI-011 | Entities use `has_entity_name` and stable unique IDs based on the config entry and sub-entry IDs. | implemented |
| HAI-012 | Minimum Home Assistant version: 2026.10.0 (as in `hacs.json`), Python 3.14. | implemented |
| HAI-013 | Every entity has a meaningful icon from `icons.json`, with state-dependent icons for enums. | implemented |
| HAI-015 | Multi-step dialogs mark every step but the last as not final, so the button reads "Next" instead of "Submit". Home Assistant has no "Back" button in setup dialogs; everything can be changed later with the gear icon. | implemented |
| HAI-016 | Dialogs show only what is needed. Where one answer decides several inputs, a question comes first and the next step asks only for those inputs; otherwise optional inputs sit in collapsible sections (Home Assistant cannot hide fields depending on another field of the same step). A section is open when it already holds a value, so editing never hides what was set. Applies to setup, options and reconfigure. | implemented |
| HAI-018 | House setup and options: step 1 name (setup only), heating type, outdoor sensor; step 2 asks two questions and the living area: *Do you know the heat load from a calculation?* (yes/no) and *Is the flow temperature measured?* (no / flow / flow and return). Only on *yes* a step asks heat load, design outdoor temperature and share outside Thermogeist; only with a measurement a step asks the one or two sensors. In the options the answers are pre-selected from the current values; answering *no* clears the inputs that belong to it. | implemented |
| HAI-019 | Room basics: name, area, room sensor, share mode visible; section *Windows and devices* (window contacts, heat sources) and section *More* (design indoor temperature) collapsed. Size and position: the lowest point under a sloped ceiling sits in a collapsed section *Sloped ceiling*. Heat source factors: the number per device visible, the factor sensors in a collapsed section. | implemented |
| HAI-020 | Thermostat roles: *How to control* always visible. If a profile or the Zigbee2MQTT detection found roles, they sit in a collapsed section *Detected roles – check if you like*; otherwise they are shown open. Valve confirmation interval and calibration roles sit in a collapsed section *More*. | implemented |
| HAI-021 | Adding a room ends with the question *Add a thermostat* / *Done*; each thermostat goes through the usual device and roles steps and returns to that question. The room is saved with its thermostats at *Done*, so users do not have to find the gear icon to add the first thermostat. | implemented |
| HAI-014 | Device models are "Thermogeist House" and "Thermogeist Room" (model names cannot be translated in HA, so they are neutral product names). | implemented |
| HAI-017 | After setup, every entity of the house that this setup did not create is removed from the entity registry: entities of removed rooms and thermostats, and entities a thermostat no longer has after editing (e.g. its valve position when no position can be read or derived). No stale "unavailable" entities remain. | implemented |
