# SCN-HOUSE-010: A weather entity can serve as outdoor temperature

**Spec:** MDL-008
**Test:** `tests/ha/test_rooms.py::test_weather_entity_as_outdoor_temperature`

## Initial state
A house whose outdoor temperature is `weather.forecast_home` (state `cloudy`, attribute
`temperature` 5 °C), a room with known heat loss.

## Steps
1. Read the room's heat demand.
2. The weather entity reports 0 °C.

## Expected result
1. The demand is computed with 5 °C outside.
2. It rises accordingly.

## Why it matters
Almost every Home Assistant has a weather entity; nobody needs an outdoor sensor to start.
