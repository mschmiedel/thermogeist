# Documentation

User documentation is written for people, not for engineers: task-oriented, with examples and
screenshots, technical terms explained on first use.

## Requirements

| ID | Requirement | Status |
|---|---|---|
| DOC-001 | User-facing docs are multilingual. English is the default, German is maintained alongside. | implemented |
| DOC-002 | `README.md` (English) and `README.de.md` (German), each linking to the other at the top. | implemented |
| DOC-003 | `docs/en/` and `docs/de/` share the same file structure and file names. | implemented |
| DOC-004 | Every reason code and every diagnosis has an FAQ entry in both languages (see RSN-005). | in progress |
| DOC-005 | A change to user-facing text updates both languages in the same change. A test checks that both doc trees contain the same files. | implemented |
| DOC-006 | HA UI texts come from `translations/en.json` and `translations/de.json` with identical keys. | implemented |

## Planned structure

```
docs/
  en/
    getting-started.md
    concepts.md          house, groups, rooms, heating types
    devices.md           supported thermostats and their limits
    calibration.md
    faq/                 one file per reason code / diagnosis
  de/
    (same files)
```

Specs, test scenarios and agent docs are English only.
