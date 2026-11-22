# SCN-SETUP-008: Questions decide which details are asked

**Spec:** HAI-016, HAI-018
**Test:** `tests/ha/test_config_flow.py::test_questions_decide_the_details`

## Initial state
Step 1 of the house setup completed.

## Steps
1. Answer: heat load not known, flow and return measured.
2. Choose both sensors.
3. Open the options: change the answer to "not measured".

## Expected result
1. No heat load step; the next step asks exactly the flow and the return sensor.
2. The house is created.
3. The options pre-select "not known" and "flow and return"; after the change both sensors
   are cleared.

## Why it matters
People without a heat load calculation or flow sensor see no fields they cannot fill in.
