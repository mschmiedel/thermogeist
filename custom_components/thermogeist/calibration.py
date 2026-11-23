# SPDX-License-Identifier: MIT
"""Lost calibration: HA glue for ``core.calibration`` (spec DIA-024).

The entity is the thermostat's ``calibration_status`` role, or the profile's expose found on
the device (thermostats added before the profile knew it). The values are the ones set in the
dialog, or the profile's for thermostats saved before the dialog had the field.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from .const import DOMAIN
from .core.actuator import Z2M_UNIQUE_ID_SUFFIX, DeviceProfile, Role, Source, Thermostat
from .core.calibration import CalibrationWatch, is_uncalibrated

if TYPE_CHECKING:
    from .runtime import HouseRuntime

CHECK_EVERY = timedelta(minutes=1)
"""DIA-024: how often a lasting "not calibrated" is checked."""


class CalibrationManager:
    """Raises a repair issue while a thermostat reports that it is not calibrated."""

    def __init__(
        self, hass: HomeAssistant, runtime: HouseRuntime, profiles: list[DeviceProfile]
    ) -> None:
        self._hass = hass
        self._runtime = runtime
        self._profiles = {p.profile_id: p for p in profiles}
        self._sources: dict[str, tuple[str, tuple[str, ...]]] = {}
        self._watches: dict[str, CalibrationWatch] = {}

    def lost(self, tid: str) -> bool:
        watch = self._watches.get(tid)
        return watch is not None and watch.lost

    @callback
    def async_start(self) -> list[CALLBACK_TYPE]:
        for tid, thermostat in self._runtime.thermostats.items():
            if (source := self._source(thermostat)) is not None:
                self._sources[tid] = source
                self._watches[tid] = CalibrationWatch()
        if not self._sources:
            return []
        self._hass.async_create_task(self._async_check())
        entities = [entity for entity, _ in self._sources.values()]
        return [
            async_track_state_change_event(self._hass, entities, self._on_change),
            async_track_time_interval(self._hass, self._on_interval, CHECK_EVERY),
        ]

    def _source(self, thermostat: Thermostat) -> tuple[str, tuple[str, ...]] | None:
        profile = self._profiles.get(thermostat.profile_id or "")
        mapping = (
            profile.roles.get(Source.Z2M, {}).get(Role.CALIBRATION_STATUS) if profile else None
        )
        values = thermostat.uncalibrated
        if values is None:
            values = mapping.uncalibrated if mapping else ()
        if not values:
            return None
        entity = thermostat.roles.get(Role.CALIBRATION_STATUS)
        if entity is None and mapping is not None:
            entity = self._device_entity(thermostat, mapping.expose)
        return (entity, values) if entity else None

    def _device_entity(self, thermostat: Thermostat, expose: str) -> str | None:
        if thermostat.device_id is None:
            return None
        marker = f"_{expose}{Z2M_UNIQUE_ID_SUFFIX}"
        entries = er.async_entries_for_device(er.async_get(self._hass), thermostat.device_id)
        return next((e.entity_id for e in entries if e.unique_id.endswith(marker)), None)

    @callback
    def _on_change(self, _event: Event[EventStateChangedData]) -> None:
        self._hass.async_create_task(self._async_check())

    @callback
    def _on_interval(self, _now: datetime) -> None:
        self._hass.async_create_task(self._async_check())

    async def _async_check(self) -> None:
        now = self._runtime.now()
        changed = False
        for tid, (entity, values) in self._sources.items():
            state = self._hass.states.get(entity)
            shown = (
                None
                if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
                else state.state
            )
            watch = self._watches[tid]
            if watch.update(is_uncalibrated(shown, values), now):
                changed = True
                await self._async_report(tid, lost=watch.lost)
        if changed:
            self._runtime.notify()

    async def _async_report(self, tid: str, *, lost: bool) -> None:
        thermostat = self._runtime.thermostats[tid]
        room = self._runtime.rooms[thermostat.room_id].room.name
        issue_id = f"thermostat_not_calibrated_{tid}"
        if not lost:
            ir.async_delete_issue(self._hass, DOMAIN, issue_id)
            await self._runtime.control.async_logbook(
                room, "logbook_calibrated_again", thermostat=thermostat.name
            )
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="thermostat_not_calibrated",
            translation_placeholders={"thermostat": thermostat.name, "room": room},
            learn_more_url=f"{self._runtime.docs_url}/en/faq/thermostat_not_calibrated.md",
        )
        await self._runtime.control.async_logbook(
            room, "logbook_not_calibrated", thermostat=thermostat.name
        )
