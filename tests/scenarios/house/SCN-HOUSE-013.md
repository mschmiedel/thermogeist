# SCN-HOUSE-013: Flow temperature from the heating curve without a flow sensor

**Spec:** MDL-019, DIA-014
**Test:** `tests/ha/test_house_sensors.py::test_flow_from_the_heating_curve`

## Initial state
A house without flow sensor, with the curve −10 °C → 45 °C, 15 °C → 30 °C, 5 °C outside and a
design temperature of −10.5 °C.

## Steps
1. Read the flow temperature sensor of the house.
2. Read the flow on the design day.

## Expected result
1. 36 °C, with source `heating_curve`.
2. 45 °C, with source `heating_curve`; there is no spread sensor.

## Why it matters
Most people have no flow sensor but can read the curve off their heat generator; the controller
and the radiator sizing then work with a real flow temperature instead of guessing.
