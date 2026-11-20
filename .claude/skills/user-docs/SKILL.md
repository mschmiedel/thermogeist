---
name: user-docs
description: Write or update user-facing documentation, README files, FAQ entries and HA UI translations in English and German. Use whenever user-visible behaviour, texts or reason codes change.
---

# Write user documentation

## Languages

- English is the default, German is maintained alongside. Always update both in the same change.
- `README.md` ↔ `README.de.md`, `docs/en/<file>` ↔ `docs/de/<file>` (same file names),
  `translations/en.json` ↔ `translations/de.json` (same keys).
- German: natural, informal "du", no literal translation of English idioms.

## Style

- Task-oriented: "How do I …", not "The component consists of …".
- Start with what the user sees and wants, then how to do it, then background.
- Explain technical terms on first use (e.g. "opening point – the valve position at which water
  starts to flow").
- Concrete examples with real-looking values. Short sentences. One idea per paragraph.
- Never blame the user; say what to check and what to do.

## FAQ entries

Every reason code and every diagnosis has one FAQ file per language under `docs/<lang>/faq/`:

1. **What you see** – the message as shown in HA.
2. **What it means** – plain language.
3. **What to check** – ordered from most likely to least likely.
4. **What to do** – concrete steps, including when to call a professional (e.g. hydraulic
   balancing, procedure B).
