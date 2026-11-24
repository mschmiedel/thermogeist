# SCN-DEV-001: The BTH-RA model reproduces a recorded day

**Spec:** TST-012
**Test:** `tests/core/test_device_models.py::test_bth_ra_model_reproduces_the_recorded_day`

## Initial state
`tests/fixtures/devices/bosch_bth_ra_day.csv`: one day of a Bosch Radiator Thermostat II in a guest bathroom regulating itself on an external room temperature, setpoint 19.5 °C, 10-minute samples.

## Steps
1. Feed the recorded setpoint and temperature into `BthRaModel`, starting from the first recorded valve position.

## Expected result
- The model's valve differs from the recorded one by at most 4 % on average (fitted: 3.1 %).

## Why it matters
The setpoint strategy can be tested against how this thermostat really regulates: it integrates, opens by 2.9 % per kelvin and minute and closes about 2.5 times as fast.
