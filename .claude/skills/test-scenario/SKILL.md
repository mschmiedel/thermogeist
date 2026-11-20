---
name: test-scenario
description: Write a documented, deterministic test scenario (markdown + pytest) using the TimeProvider pattern. Use for any learning, timing, debounce, override, safety or control behaviour test.
---

# Write a test scenario

## 1. Document it

Create `tests/scenarios/<feature>/SCN-<FEATURE>-<NNN>.md` from the template in
`tests/scenarios/README.md`. Pick the next free number for that feature; never reuse IDs.
Write it so a non-programmer understands what is checked and why it matters to the user.

## 2. Implement it

- Put the test in `tests/` mirroring the core structure, e.g. `tests/core/test_<module>.py`.
- The docstring contains exactly `Scenario: SCN-<FEATURE>-<NNN>`.
- Use `FakeTimeProvider` with a fixed, timezone-aware start time. Move time only with
  `advance(...)`. Never sleep, never read the real clock.
- Express durations as named `timedelta`s in the test (`WINDOW_DELAY = timedelta(seconds=30)`),
  and test both sides of every threshold (just before, just after).
- For control and learning behaviour, run the room simulator for simulated hours or days and
  assert on the metrics from `spec/test-strategy.md` (overshoot, settling time, valve moves).
- Assert reason codes, not log strings.

## 3. Check

`.venv/bin/pytest` – `tests/test_scenario_coverage.py` fails if markdown and tests disagree.

## Good scenario candidates

- threshold edges (sensor stale at 59:59 vs 60:00)
- restarts in the middle of a process (calibration, override)
- conflicting reasons at the same time (precedence)
- learning that should *not* happen (window open, override active)
- device misbehaviour (ignored command, stale report, recalibration)
