# SCN-SIZING-004: Hours are closed from minute samples

**Spec:** DIA-014, DIA-015
**Test:** `tests/core/test_sizing.py::test_hour_collector`

## Initial state
An empty hour collector.

## Steps
1. Add 60 minute samples from 10:00: outdoor 3 °C, flow 38 °C (with one 60 °C hot water
   spike), rooms 20 °C; the living room fully open in the cold for 55 minutes, the bathroom for
   50 minutes.
2. Add the first sample of 11:00.
3. Repeat an hour with flow 23 °C (heating off).

## Expected result
- The 10:00 hour closes at 11:00 with outdoor 3 °C and flow 38 °C (median ignores the spike).
- Only the living room counts as fully open (55/60 ≥ 90 %, 50/60 < 90 %).
- The hour with flow 23 °C has no curve value (less than 5 K above the rooms).
- "Fully open in the cold" needs valve ≥ 95 %, room more than 0.5 K below target, outdoor below
  5 °C and the reason `setpoint`.

## Why it matters
Hot water spikes and summer hours must not bend the learned heating curve.
