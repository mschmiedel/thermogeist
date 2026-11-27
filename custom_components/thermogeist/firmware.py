# SPDX-License-Identifier: MIT
"""Minimum firmware: HA glue for ``core.firmware`` (spec ACT-017).

The installed version is the one Home Assistant shows for the device (``sw_version``). The
check runs at start and whenever one of the thermostats' device entries changes, e.g. after a
firmware update.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .core.actuator import DeviceProfile
from .core.firmware import firmware_too_old

if TYPE_CHECKING:
    from .runtime import HouseRuntime

ISSUE_PREFIX = "thermostat_firmware_old_"


class FirmwareManager:
    """Raises a repair issue while a thermostat runs older firmware than its profile names."""

    def __init__(
        self, hass: HomeAssistant, runtime: HouseRuntime, profiles: list[DeviceProfile]
    ) -> None:
        self._hass = hass
        self._runtime = runtime
        self._profiles = {p.profile_id: p for p in profiles}

    @callback
    def async_start(self) -> list[CALLBACK_TYPE]:
        self._check()
        return [
            self._hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, self._on_device_changed)
        ]

    @callback
    def _on_device_changed(self, event: Event[dr.EventDeviceRegistryUpdatedData]) -> None:
        device_ids = {t.device_id for t in self._runtime.thermostats.values()}
        if event.data.get("device_id") in device_ids:
            self._check()

    @callback
    def _check(self) -> None:
        devices = dr.async_get(self._hass)
        old: set[str] = set()
        for tid, thermostat in self._runtime.thermostats.items():
            profile = self._profiles.get(thermostat.profile_id or "")
            device = devices.async_get(thermostat.device_id) if thermostat.device_id else None
            if profile is None or device is None:
                continue
            if firmware_too_old(device.sw_version, profile.min_firmware):
                old.add(tid)
                self._report(tid, device.sw_version or "", profile.min_firmware or "")
        self._remove_others(old)

    def _report(self, tid: str, installed: str, required: str) -> None:
        thermostat = self._runtime.thermostats[tid]
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            self._issue_id(tid),
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="thermostat_firmware_old",
            translation_placeholders={
                "thermostat": thermostat.name,
                "room": self._runtime.rooms[thermostat.room_id].room.name,
                "installed": installed,
                "required": required,
            },
            learn_more_url=f"{self._runtime.docs_url}/en/faq/thermostat_firmware_old.md",
        )

    def _issue_id(self, tid: str) -> str:
        return f"{ISSUE_PREFIX}{self._runtime.entry_id}_{tid}"

    def _remove_others(self, keep: set[str]) -> None:
        """Issues of this house's thermostats that are up to date now or were removed."""
        prefix = f"{ISSUE_PREFIX}{self._runtime.entry_id}_"
        wanted = {self._issue_id(tid) for tid in keep}
        for domain, issue_id in list(ir.async_get(self._hass).issues):
            if domain == DOMAIN and issue_id.startswith(prefix) and issue_id not in wanted:
                ir.async_delete_issue(self._hass, DOMAIN, issue_id)
