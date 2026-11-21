# SCN-SIZING-003: Radiator size from inputs, overruled by operation

**Spec:** DIA-004, DIA-005, DIA-010, DIA-012, DIA-023, MDL-015
**Test:** `tests/core/test_sizing.py::test_assessment`

## Initial state
A living room with 39.4 W/K heat loss, setpoint 21.5 °C, design outdoor temperature −10.5 °C,
a 2165 W radiator, spread 2.9 K, learned flow on the design day 41.3 °C.

## Steps
1. Assess it.
2. Assess the same room with 20 000 W of radiators; once for a heat pump, once for a boiler.
3. Assess it without heat load and without flow sensor.
4. Assess the room with a 6000 W radiator (right size) whose valve was fully open in the cold for 6 hours this week.

## Expected result
1. Undersized (about 1262 W demand, 591 W output, load about 213 %), `cause: radiator_small`,
   `basis: static`, confidence *medium*.
2. Heavily oversized; with a heat pump `reserve`, with a boiler not.
3. Not assessable, `missing` names heat load, flow temperature (and not the curve).
4. Undersized with `basis: operation` and `cause: input_or_hydraulics`.

## Why it matters
The user learns whether a room can reach its setpoint in winter and what is the likely reason.
