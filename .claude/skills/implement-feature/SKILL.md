---
name: implement-feature
description: Spec-first workflow for building or changing any behaviour in this integration. Use whenever a feature, rule, controller change, adapter or bug fix changes what the product does.
---

# Implement a feature (spec-first)

1. **Find the spec.** Locate the requirement IDs in `spec/` that cover the change. If none fit,
   add requirements to the matching feature file (or a new feature file listed in
   `spec/README.md`). Status `in progress`.
2. **Clarify before coding.** If the spec leaves a user-visible choice open (defaults,
   thresholds, wording), ask the user. Do not invent defaults silently; if a default is chosen,
   name the constant and justify it in the spec.
3. **Write scenarios first.** For each meaningful behaviour, use the `test-scenario` skill to
   create `tests/scenarios/<feature>/SCN-...md`.
4. **Implement in the core.** Plain Python under `custom_components/thermogeist/core/`.
   - Time only via an injected `TimeProvider`.
   - Every change to an actuator goes through the decision point and carries a reason code. New
     codes go into the reason catalogue with en/de text and an FAQ entry (`user-docs` skill).
5. **HA layer last.** Keep it thin: wiring, entities, translations.
6. **Verify.** `.venv/bin/pytest` and `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
   must pass.
7. **Update the spec.** Set status to `implemented` only for requirements with code and tests.
   The spec must describe the state after the change, nothing historical.
8. **Credits.** If an idea or code came from another project, add it to `CREDITS.md`.
9. **User docs.** If user-visible behaviour changed, update `docs/en/` and `docs/de/` together.
