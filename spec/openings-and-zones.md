# Openings and neighbouring zones

An open door couples a room to its neighbour. For a small room next to an unheated zone (e.g. a
guest bathroom next to the entrance hall), the room's heat loss rises several times while the
door is open, and its radiator effectively heats the neighbour too. Windows are the same
mechanism towards the outside.

## Model

| ID | Requirement | Status |
|---|---|---|
| OPN-001 | An **opening** connects a room to another zone: the outside (window) or a neighbouring room. Window rules (RUL-010) and doors use the same logic: contact sensor, open/close delays, reason code. | planned |
| OPN-002 | Neighbouring zones can be rooms without a thermostat (MDL-037), optionally with their own temperature sensor; without one, their temperature is estimated between room and outdoor temperature. | planned |
| OPN-003 | Per door, the user chooses what happens while it is open: **couple** (keep heating; the model knows the higher loss), **limit** (milder than a window, e.g. setback by a few kelvin) or **ignore**. Default: couple. | planned |
| OPN-004 | Reason codes `door_open_coupled` and `door_open_limited`, with FAQ pages in both languages. | planned |

## Learning and control

| ID | Requirement | Status |
|---|---|---|
| OPN-010 | With a door sensor, the room's heat loss is learned separately for door closed and door open; the extra loss towards the neighbour is shown as its own value (W/K). | planned |
| OPN-011 | Without a door sensor, phases where the room cools clearly faster than the model expects are flagged as "probably door open". This is a hint only and never triggers a rule. | planned |
| OPN-012 | When a door opens, the feed-forward switches to the open-door heat loss at once instead of waiting for the room to cool down. | planned |

## Diagnostics

| ID | Requirement | Status |
|---|---|---|
| OPN-020 | Show how much of a room's heat goes to a neighbour while the door is open, e.g. "Guest bathroom: about 60 % of its heat goes to the hall when the door is open". | planned |
| OPN-021 | Recommend a door sensor where it pays off: small rooms next to cold zones, where the open-door loss is a large multiple of the closed-door loss. | planned |
