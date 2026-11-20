# Working rules for agents

This repository is developed spec-first. This file is the binding guide for Claude and other
agents. `CLAUDE.md` points here.

## Principles

1. **Spec first.** `spec/` always describes the current state of the product, one file per
   feature. Every behaviour change starts by changing the matching spec and ends with the spec's
   status being correct. No tickets, no change history in the spec: history lives in Git.
2. **Keep status honest.** Every requirement in a spec has a status: `planned`, `in progress`,
   `implemented`, `rejected`. `implemented` only when code and tests exist.
3. **Never read the clock directly.** No `datetime.now()`, `time.time()`, `time.monotonic()` or
   `asyncio.sleep()` for logic in the core. Always go through `TimeProvider`
   (see `spec/test-strategy.md`).
4. **Document test scenarios.** Every meaningful test scenario has an ID and a description in
   `tests/scenarios/<feature>/`. The test references the ID in its docstring.
5. **Every decision has a reason.** When the controller or a rule changes anything, it produces a
   reason code with parameters and text (see `spec/decisions-and-reasons.md`). No silent
   shutdown, throttling or override.
6. **Core without Home Assistant.** Domain logic lives in `custom_components/<domain>/core/` and
   imports nothing from `homeassistant`. The HA layer is thin and only translates.
7. **Users first.** Texts, error messages and docs address people without control-engineering
   knowledge. Technical terms only with an explanation.

## License and provenance

- Everything is MIT. Every source file starts with `# SPDX-License-Identifier: MIT`.
- Ideas or code taken from or closely based on other projects are listed in `CREDITS.md`, with
  project, license and what exactly was used.
- Only code under a compatible license (MIT, BSD, Apache-2.0) may be copied.

## Language

- Everything in the repository is written in English: specs, test scenarios, agent docs, code,
  comments, commit messages.
- User-facing documentation (`README.md`, `docs/`) and UI texts are multilingual: English is the
  default, German is maintained alongside.
  - `README.md` (English) and `README.de.md` (German), linked to each other at the top.
  - `docs/en/` and `docs/de/` with the same file structure.
  - HA translations in `custom_components/<domain>/translations/en.json` and `de.json`.
  - A change to user-facing text updates both languages in the same change.

## Quality

- Python 3.14+ (required by Home Assistant 2026.10), type hints everywhere, `ruff` (lint + format) must be clean.
- `pytest` must be green before anything counts as `implemented`.
- Small, well-named functions. No magic numbers in the core: name constants and justify them in
  the spec.

## Commands

```bash
python3.14 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check . && .venv/bin/ruff format --check .
scripts/build_zip.sh
```

## Skills

Project skills live in `.claude/skills/`. Use the matching skill for recurring workflows:
`implement-feature`, `test-scenario`, `actuator-adapter`, `release`, `maintain-spec`,
`user-docs`.

## Still open

- Product name is **Thermogeist** (domain `thermogeist`). Trademark and collision check still
  pending (see `spec/open-questions.md`). The local folder is still named `ha-thermostat`.
- Repository: https://github.com/mschmiedel/thermogeist (public). Push and release only when the
  user asks.
