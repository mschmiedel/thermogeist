# SCN-SIZING-005: The room shows its radiator size and a repair issue when too small

**Spec:** DIA-012, DIA-013, DIA-014
**Test:** `tests/ha/test_sizing.py::test_undersized_room_sensor_and_issue`

## Initial state
A house with heat load, flow sensor and a room with a small radiator; 60 learned hours of a
heating curve are stored.

## Steps
1. Start Home Assistant.
2. Change the radiator so it is large enough, then reload.

## Expected result
1. *Radiator size* is `undersized` with `cause: radiator_small`; the house shows *Flow on the
   design day*; a repair issue *radiator undersized* exists with an FAQ link.
2. The sensor shows `right_size` and the repair issue is gone.

## Why it matters
A room that cannot reach its setpoint in winter should be visible before winter.
