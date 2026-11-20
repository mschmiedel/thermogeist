# SPDX-License-Identifier: MIT
"""Meta test: every documented scenario has a test and vice versa (spec TST-020, TST-021)."""

import re
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SCENARIO_DIR = TESTS_DIR / "scenarios"
ID_PATTERN = re.compile(r"SCN-[A-Z]+-\d{3}")
HEADING_PATTERN = re.compile(r"^# (SCN-[A-Z]+-\d{3}):", re.MULTILINE)
TEST_REFERENCE_PATTERN = re.compile(r"Scenario: (SCN-[A-Z]+-\d{3})")


def _documented_ids() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in SCENARIO_DIR.rglob("SCN-*.md"):
        match = HEADING_PATTERN.search(path.read_text(encoding="utf-8"))
        assert match, f"{path} has no '# SCN-...:' heading"
        assert match.group(1) == path.stem, f"{path}: heading ID does not match file name"
        assert match.group(1) not in found, f"duplicate scenario ID {match.group(1)}"
        found[match.group(1)] = path
    return found


def _referenced_ids() -> set[str]:
    referenced: set[str] = set()
    for path in TESTS_DIR.rglob("test_*.py"):
        referenced.update(TEST_REFERENCE_PATTERN.findall(path.read_text(encoding="utf-8")))
    return referenced


def test_every_scenario_has_a_test() -> None:
    missing = set(_documented_ids()) - _referenced_ids()
    assert not missing, f"scenarios without a test: {sorted(missing)}"


def test_every_referenced_scenario_is_documented() -> None:
    unknown = _referenced_ids() - set(_documented_ids())
    assert not unknown, f"tests reference undocumented scenarios: {sorted(unknown)}"


def test_scenario_ids_are_well_formed() -> None:
    for scenario_id in _documented_ids():
        assert ID_PATTERN.fullmatch(scenario_id)
