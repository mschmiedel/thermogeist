# SPDX-License-Identifier: MIT
"""Guards for architecture and licensing rules (spec ARC-001, ARC-002, AGENTS.md)."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
INTEGRATION_DIR = ROOT / "custom_components" / "thermogeist"
CORE_DIR = INTEGRATION_DIR / "core"
CLOCK_MODULE = CORE_DIR / "time_provider.py"

HA_IMPORT = re.compile(r"^\s*(from|import)\s+homeassistant\b", re.MULTILINE)
DIRECT_CLOCK = re.compile(
    r"datetime\.now\(|datetime\.utcnow\(|time\.time\(|time\.monotonic\(|asyncio\.sleep\("
)
SPDX_HEADER = "# SPDX-License-Identifier: MIT"


def _python_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def test_core_does_not_import_home_assistant() -> None:
    offenders = [p for p in _python_files(CORE_DIR) if HA_IMPORT.search(p.read_text())]
    assert not offenders, f"core imports homeassistant: {offenders}"


def test_core_reads_time_only_through_time_provider() -> None:
    offenders = [
        p
        for p in _python_files(CORE_DIR)
        if p != CLOCK_MODULE and DIRECT_CLOCK.search(p.read_text())
    ]
    assert not offenders, f"direct clock access outside TimeProvider: {offenders}"


def test_every_python_file_has_spdx_header() -> None:
    files = _python_files(INTEGRATION_DIR) + _python_files(ROOT / "tests")
    offenders = [p for p in files if not p.read_text().startswith(SPDX_HEADER)]
    assert not offenders, f"missing SPDX header: {offenders}"
