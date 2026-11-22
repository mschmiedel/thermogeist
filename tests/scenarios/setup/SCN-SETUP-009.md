# SCN-SETUP-009: The heating curve instead of a flow sensor

**Spec:** MDL-019, HAI-018
**Test:** `tests/ha/test_config_flow.py::test_heating_curve_instead_of_a_flow_sensor`

## Initial state
Step 1 of the house setup completed.

## Steps
1. Answer: heat load not known, flow not measured but the heating curve is known.
2. Enter a curve whose flow rises when it gets warmer, then a correct one.
3. Open the options and choose a flow sensor instead.

## Expected result
1. The next step asks exactly the four curve values.
2. First an error on the warm flow field, then the house is created with the curve.
3. The options pre-select the curve; after the change the curve values are cleared.

## Why it matters
The curve is the one value almost everyone can read off their heat generator.
