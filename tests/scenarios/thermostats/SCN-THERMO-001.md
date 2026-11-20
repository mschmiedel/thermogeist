# SCN-THERMO-001: A Sonoff TRVZB is recognised and gets a planned position

**Spec:** HAI-006, ACT-031 to ACT-033, ACT-014, CTL-030, MDL-007
**Test:** `tests/ha/test_thermostats.py::test_sonoff_is_recognised_and_planned`

## Initial state
House 6.5 kW at −10.5 °C, 160 m², flow sensor 40 °C, outdoor 5 °C. Room "Living room" 20 m² at 19.5 °C. A Zigbee2MQTT device "Living TRV" (SONOFF, TRVZB).

## Steps
1. Add thermostat: room, device, radiator 2000 W.
2. Accept the pre-filled roles.

## Expected result
- Profile "Sonoff TRVZB"; climate, valve opening and closing degree are pre-filled.
- Planned valve position ≈ 68 % (feed-forward ≈ 60.6 % + proportional 7.5 %), mode observe, strategy valve.
- Kind sensor shows valve-based.

## Why it matters
Assigning a known thermostat takes three clicks and immediately shows what Thermogeist would do.
