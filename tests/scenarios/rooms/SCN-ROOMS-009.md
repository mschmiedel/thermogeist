# SCN-ROOMS-009: The feed-forward subtracts device heat and follows a device switching off

**Spec:** MDL-040, MDL-043, MDL-044
**Test:** `tests/ha/test_heat_sources.py::test_feed_forward_subtracts_device_heat`

## Initial state
A room with a 1500 W radiator, flow 40 °C, and a gaming PC at 300 W as heat source.

## Steps
1. Look at the planned valve position.
2. The PC switches off; 11 minutes pass.

## Expected result
- `heat_from_devices_w: 300` and a share of the demand covered by devices.
- After the 10-minute average: `heat_from_devices_w: 0` and a higher feed-forward.

## Why it matters
When the PC goes off, the radiator takes over within minutes, not after hours of slow correction.
