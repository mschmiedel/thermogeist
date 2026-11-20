# SPDX-License-Identifier: MIT
"""English and German UI texts must cover the same keys (spec HAI-010, DOC-006)."""

import json
from pathlib import Path

TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / "thermogeist" / "translations"


def _keys(node: object, prefix: str = "") -> set[str]:
    if not isinstance(node, dict):
        return {prefix}
    keys: set[str] = set()
    for key, value in node.items():
        keys |= _keys(value, f"{prefix}.{key}" if prefix else key)
    return keys


def _load(language: str) -> dict:
    return json.loads((TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))


def test_english_and_german_have_the_same_keys() -> None:
    english, german = _keys(_load("en")), _keys(_load("de"))
    assert english - german == set(), "missing in de.json"
    assert german - english == set(), "missing in en.json"


def test_every_validation_code_has_a_text() -> None:
    from custom_components.thermogeist.core.house import (
        FIELD_DESIGN_TEMPERATURE,
        FIELD_HEAT_LOAD,
        FIELD_LIVING_AREA,
        FIELD_SHARE_OUTSIDE,
    )

    codes = {"name_empty", "design_temperature_required"} | {
        f"{field}_out_of_range"
        for field in (
            FIELD_HEAT_LOAD,
            FIELD_DESIGN_TEMPERATURE,
            FIELD_SHARE_OUTSIDE,
            FIELD_LIVING_AREA,
        )
    }
    for language in ("en", "de"):
        errors = _load(language)["config"]["error"]
        assert codes <= errors.keys(), f"{language}: missing {codes - errors.keys()}"


def test_docs_exist_in_both_languages() -> None:
    """Spec DOC-005: docs/en and docs/de contain the same files."""
    docs = Path(__file__).parent.parent / "docs"
    english = {p.relative_to(docs / "en") for p in (docs / "en").rglob("*.md")}
    german = {p.relative_to(docs / "de") for p in (docs / "de").rglob("*.md")}
    assert english == german


def test_every_reason_code_has_texts_and_faq() -> None:
    """Spec RSN-005, DOC-004: translated state and FAQ page in both languages."""
    from custom_components.thermogeist.core.decisions import CATALOGUE, ReasonCode

    docs = Path(__file__).parent.parent / "docs"
    assert set(CATALOGUE) == set(ReasonCode)
    for language in ("en", "de"):
        states = _load(language)["entity"]["sensor"]["active_reason"]["state"]
        for code in ReasonCode:
            assert code.value in states, f"{language}: no text for {code}"
            assert (docs / language / "faq" / f"{code.value}.md").is_file(), f"{language}: no FAQ"


def test_every_named_entity_has_an_icon() -> None:
    """Spec HAI-013."""
    icons = json.loads((TRANSLATIONS.parent / "icons.json").read_text(encoding="utf-8"))["entity"]
    for platform, entities in _load("en")["entity"].items():
        for key in entities:
            assert key in icons.get(platform, {}), f"no icon for {platform}.{key}"
