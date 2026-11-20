# Test scenarios

Every meaningful test scenario is documented here, one file per scenario, grouped by feature.
The file explains the scenario in plain language so it can be reviewed without reading code.

## Rules

- File path: `tests/scenarios/<feature>/<ID>.md`, e.g. `time-provider/SCN-TIME-001.md`.
- ID format: `SCN-<FEATURE>-<NNN>`. IDs are never reused.
- The test that implements the scenario contains `Scenario: <ID>` in its docstring.
- `tests/test_scenario_coverage.py` fails if a scenario has no test or a test names an unknown
  scenario.

## Template

```markdown
# SCN-<FEATURE>-<NNN>: <short title>

**Spec:** <requirement IDs, e.g. TST-003>
**Test:** `tests/<path>.py::<test_name>`

## Initial state
What is set up before the scenario starts (time, room, device, settings).

## Steps
1. What happens, with simulated times (e.g. "after 30 s", "on day 3").

## Expected result
What must be true afterwards, including reason codes where relevant.

## Why it matters
One or two sentences on the user-visible behaviour this protects.
```
