# Calibration mode

The opening point (the valve percentage at which water actually starts to flow) varies with the
valve body, presetting and the TRV's stroke calibration; 10–20 % has been observed. Calibration
mode measures it on purpose. The pipe sensor is meant for calibration only and moves from room to
room; it is not installed permanently.

## Procedure

| ID | Step | Status |
|---|---|---|
| CAL-001 | The user attaches a temperature probe to the flow pipe right at the valve and assigns it to the room (selector). | planned |
| CAL-002 | Check preconditions: heating is running, flow clearly above room temperature, room has headroom. Otherwise no start, with a reason. | planned |
| CAL-003 | Fulfil the adapter's preconditions (e.g. child lock off), optionally trigger the device's stroke calibration and wait for it. | planned |
| CAL-004 | Run a step sequence up and down, twice. Detect flow onset from the pipe temperature rise. | planned |
| CAL-005 | Store the result: opening point, direction difference, scatter, date, probe used. Visible in the room. | planned |
| CAL-007 | The measured opening point and scatter set the thermostat's minimum opening (CTL-023). | planned |
| CAL-006 | Restore the device state (ACT-008). Can be aborted at any time, cleanly even after a restart. | planned |

## Recalibration recommended

| ID | Trigger | Status |
|---|---|---|
| CAL-010 | Battery change or TRV recalibration detected | planned |
| CAL-011 | Presetting changed (confirmed by the user) | planned |
| CAL-012 | Learned valve characteristic drifts | planned |

Without calibration, the integration learns slowly from room temperature. The status then reads
"not calibrated, estimated".
