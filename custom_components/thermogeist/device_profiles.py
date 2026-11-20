# SPDX-License-Identifier: MIT
"""Load the shipped device profiles (spec ACT-030) once, outside the event loop."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .core.actuator import DeviceProfile, parse_profile

PROFILE_DIR = Path(__file__).parent / "device_profiles"
_CACHE_KEY = "device_profiles"


def _load_profiles() -> list[DeviceProfile]:
    return [
        parse_profile(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(PROFILE_DIR.glob("*.json"))
    ]


async def async_get_profiles(hass: HomeAssistant) -> list[DeviceProfile]:
    data = hass.data.setdefault(DOMAIN, {})
    if _CACHE_KEY not in data:
        data[_CACHE_KEY] = await hass.async_add_executor_job(_load_profiles)
    return data[_CACHE_KEY]
