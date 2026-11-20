# SCN-CTL-001: Heat pump with full data: calm, open valves, no big overshoot

**Spec:** CTL-010, CTL-030 to CTL-033, TST-030
**Test:** `tests/core/test_controller_simulation.py::test_heat_pump_with_full_data_is_calm_and_open`

## Initial state
Simulated room 20 m², 20 W/K, radiator 2000 W (75/65/20), opening point 10 %. Outdoor 0 °C, flow 40 °C, start 19 °C, target 20 °C. Heat-pump profile.

## Steps
1. Run 4 simulated days.

## Expected result
- Overshoot ≤ 0.4 K, within ±0.3 K after ≤ 16 h.
- Day 3: ≤ 10 valve moves, mean opening ≥ 40 %.
- Never below the 40 % minimum opening.

## Why it matters
This is the core promise: calm control that keeps the heat pump's water flowing.
