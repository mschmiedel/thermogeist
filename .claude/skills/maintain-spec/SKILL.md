---
name: maintain-spec
description: Keep spec/ an accurate description of the current state. Use after refinement sessions, design decisions, or when code and spec may have drifted apart.
---

# Maintain the spec

`spec/` describes the current state, one file per feature. It is not a ticket system and not a
changelog.

## After a refinement or design discussion

1. Turn each decision into a requirement row with an ID, in the matching feature file.
   New topic → new feature file, added to the table in `spec/README.md`.
2. Rejected ideas stay as `rejected` with a one-line reason, so they are not re-discussed.
3. Open points go to `spec/open-questions.md`, not into requirement rows.
4. Write in English, short and concrete: numbers with units, defaults named.

## Drift check

1. For every requirement marked `implemented`: is there code and a test referencing the ID or its
   scenario? If not, downgrade the status.
2. For code that has no requirement: add one or question whether the code is needed.
3. Make sure IDs are unique and never reused.

## Never

- No history ("changed on …", "previously …"): Git has it.
- No assumptions about other projects' internals beyond what is credited in `CREDITS.md`.
