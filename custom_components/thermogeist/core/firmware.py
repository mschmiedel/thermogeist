# SPDX-License-Identifier: MIT
"""Minimum firmware named by a device profile (spec ACT-017).

Thermogeist knows no feature per firmware version. A profile only names the oldest version with
which all its features work; an older device gets a warning, nothing else changes.
"""

from __future__ import annotations

import re

_VERSION = re.compile(r"\d+(?:\.\d+)*")


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """The first dotted number in a firmware text ("1.3.0", "V1.3.0 (build 7)"), else None."""
    if not text:
        return None
    match = _VERSION.search(text)
    return tuple(int(part) for part in match.group().split(".")) if match else None


def firmware_too_old(installed: str | None, minimum: str | None) -> bool:
    """True only when both versions can be read and the installed one is older.

    Missing parts count as zero, so "1.3" equals "1.3.0".
    """
    have, need = parse_version(installed), parse_version(minimum)
    if have is None or need is None:
        return False
    length = max(len(have), len(need))
    return have + (0,) * (length - len(have)) < need + (0,) * (length - len(need))
