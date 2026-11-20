# SCN-ROOMS-001: Adding a room shows its share, demand and reason

**Spec:** HAI-005, MDL-031, MDL-035, OVR-012, RSN-002
**Test:** `tests/ha/test_rooms.py::test_add_estimated_room`

## Initial state
House "Home": 6.5 kW at −10.5 °C, 160 m². Outdoor 5 °C. Room sensor reports 19.5 °C.

## Steps
1. Add room "Living room": 20 m², 2.5 m, two exterior walls, heated above and below.

## Expected result
- Room device with climate entity: current 19.5 °C, target 20 °C.
- Share 12.5 %, heat loss coefficient 26.6 W/K, heat demand ≈ 400 W.
- Active reason `setpoint`.
- House: 87.5 % not assigned to a room.

## Why it matters
The core value of M2: every room knows what it needs and says what it does.
