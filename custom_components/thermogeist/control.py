# SPDX-License-Identifier: MIT
"""Control mode: write plans to thermostats (spec ACT-040 to ACT-045, OVR-001, RSN-003, RSN-004).

This is HA glue. What to write is decided in ``core`` (controller, decisions, supervision);
this module only talks to the devices, remembers what it changed and puts it back.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.translation import async_get_translations

from .const import DOMAIN
from .core.actuator import DeviceProfile, Kind, Role, Source, Thermostat
from .core.supervision import ValveSupervisor, Verdict

if TYPE_CHECKING:
    from .runtime import HouseRuntime, RoomState

EXTERNAL_TEMPERATURE_REFRESH = timedelta(minutes=20)
"""ACT-041: Bosch falls back to its own sensor after 30 min without a value."""
EXTERNAL_TEMPERATURE_STEP_K = 0.1
OVERRIDE_DEBOUNCE_S = 20
"""OVR-002: wait until the knob has stopped turning."""
STOP_SETPOINT_C = 5.0
SETPOINT_TOLERANCE_K = 0.05
LOGBOOK_EVENT = "logbook_entry"


@dataclass(slots=True)
class ThermostatControl:
    """What Thermogeist last did with one thermostat."""

    supervisor: ValveSupervisor = field(default_factory=ValveSupervisor)
    last_setpoint_c: float | None = None
    external_value_c: float | None = None
    external_sent_at: datetime | None = None
    settings_applied: bool = False
    pending_override: CALLBACK_TYPE | None = None


class ControlManager:
    """Writes to the thermostats of controlled rooms and keeps the device state restorable."""

    def __init__(
        self, hass: HomeAssistant, runtime: HouseRuntime, profiles: list[DeviceProfile]
    ) -> None:
        self._hass = hass
        self._runtime = runtime
        self._profiles = {p.profile_id: p for p in profiles}
        self.enabled: dict[str, bool] = {}
        self.restore: dict[str, dict[str, str]] = {}
        self.thermostats: dict[str, ThermostatControl] = {
            tid: ThermostatControl() for tid in runtime.thermostats
        }

    # ----- state --------------------------------------------------------------------------

    def load(self, stored: dict[str, Any]) -> None:
        self.enabled = {
            rid: bool(on) for rid, on in stored.get("control", {}).items() if rid in self._rooms
        }
        self.restore = {tid: dict(values) for tid, values in stored.get("restore", {}).items()}

    def dump(self) -> dict[str, Any]:
        return {"control": self.enabled, "restore": self.restore}

    def is_enabled(self, room_id: str) -> bool:
        return self.enabled.get(room_id, False)

    def can_control(self, room_id: str) -> bool:
        """ACT-044: only valve-based thermostats can be controlled in M4."""
        return any(
            self._runtime.thermostats[tid].kind is Kind.VALVE
            for tid in self._rooms[room_id].thermostat_ids
        )

    @property
    def _rooms(self) -> dict[str, RoomState]:
        return self._runtime.rooms

    # ----- lifecycle ----------------------------------------------------------------------

    @callback
    def async_start(self) -> list[CALLBACK_TYPE]:
        climates = [
            t.roles[Role.CLIMATE]
            for t in self._runtime.thermostats.values()
            if Role.CLIMATE in t.roles
        ]
        return [async_track_state_change_event(self._hass, climates, self._on_device_climate)]

    async def async_set_enabled(self, room_id: str, on: bool) -> None:
        if on and not self.can_control(room_id):
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="no_valve_thermostat"
            )
        self.enabled[room_id] = on
        if on:
            for tid in self._rooms[room_id].thermostat_ids:
                ir.async_delete_issue(self._hass, DOMAIN, f"device_overrides_valve_{tid}")
        else:
            for tid in self._rooms[room_id].thermostat_ids:
                await self._async_restore(tid)
        await self._runtime.async_save()
        self._runtime.reevaluate()

    async def async_restore_orphan(self, tid: str) -> None:
        """Hand a removed thermostat's device back (ACT-008)."""
        await self._async_restore(tid)
        await self._runtime.async_save()

    # ----- applying plans -----------------------------------------------------------------

    @callback
    def schedule_apply(self) -> None:
        for room_id, on in self.enabled.items():
            if on and room_id in self._rooms:
                self._hass.async_create_task(self._async_apply(room_id))

    async def _async_apply(self, room_id: str) -> None:
        state = self._rooms[room_id]
        if state.plan is None or state.decision is None:
            return
        target = state.decision.target_setpoint_c
        for tid in state.thermostat_ids:
            thermostat = self._runtime.thermostats[tid]
            if thermostat.kind is not Kind.VALVE:
                continue
            control = self.thermostats[tid]
            if not control.settings_applied:
                await self._async_apply_settings(tid, thermostat)
                control.settings_applied = True
            if not await self._async_valve(room_id, tid, thermostat, state.plan.output_pct):
                return
            await self._async_min_opening(tid, thermostat)
            await self._async_external_temperature(thermostat, control, state)
            await self._async_setpoint(thermostat, control, target)

    async def _async_valve(
        self, room_id: str, tid: str, thermostat: Thermostat, output_pct: float
    ) -> bool:
        """Write the planned position; returns False if Thermogeist gave up on this room."""
        control = self.thermostats[tid]
        write_entity = thermostat.roles[Role.VALVE_WRITE]
        if control.supervisor.last_written_pct != output_pct:
            await self._async_write_number(tid, write_entity, output_pct)
            control.supervisor.written(output_pct)
            return True
        read_entity = thermostat.roles.get(Role.VALVE_READ, write_entity)
        verdict = control.supervisor.check(self._number(read_entity), self._runtime.now())
        if verdict is Verdict.REWRITE:
            await self._async_write_number(tid, write_entity, output_pct)
            control.supervisor.written(output_pct)
        elif verdict is Verdict.GIVE_UP:
            await self._async_give_up(room_id, tid, thermostat)
            return False
        return True

    async def _async_min_opening(self, tid: str, thermostat: Thermostat) -> None:
        entity = thermostat.roles.get(Role.VALVE_MIN)
        if entity is None:
            return
        minimum = self._runtime.controller_settings().min_opening_pct
        desired = 100.0 - minimum if thermostat.valve_min_inverted else minimum
        if self._number(entity) != desired:
            await self._async_write_number(tid, entity, desired)

    async def _async_external_temperature(
        self, thermostat: Thermostat, control: ThermostatControl, state: RoomState
    ) -> None:
        entity = thermostat.roles.get(Role.EXTERNAL_TEMPERATURE)
        room_c = state.current_temperature_c
        if entity is None or room_c is None:
            return
        value = round(room_c, 1)
        now = self._runtime.now()
        changed = (
            control.external_value_c is None
            or abs(value - control.external_value_c) >= EXTERNAL_TEMPERATURE_STEP_K
        )
        due = (
            control.external_sent_at is None
            or now - control.external_sent_at >= EXTERNAL_TEMPERATURE_REFRESH
        )
        if changed or due:
            await self._async_call("number", "set_value", entity, value=value)
            control.external_value_c = value
            control.external_sent_at = now

    async def _async_setpoint(
        self, thermostat: Thermostat, control: ThermostatControl, target: float | None
    ) -> None:
        """OVR-004: the device display shows the real room target."""
        entity = thermostat.roles[Role.CLIMATE]
        desired = STOP_SETPOINT_C if target is None else target
        current = self._climate_setpoint(entity)
        if current is None or abs(current - desired) > SETPOINT_TOLERANCE_K:
            control.last_setpoint_c = desired
            await self._async_call("climate", "set_temperature", entity, temperature=desired)
        elif control.last_setpoint_c is None:
            control.last_setpoint_c = desired

    # ----- device settings and restore (ACT-008, ACT-042) ---------------------------------

    async def _async_apply_settings(self, tid: str, thermostat: Thermostat) -> None:
        profile = self._profiles.get(thermostat.profile_id or "")
        if profile is None or thermostat.device_id is None:
            return
        entries = er.async_entries_for_device(er.async_get(self._hass), thermostat.device_id)
        for expose, value in profile.control_settings.get(Source.Z2M, ()):
            entity = next(
                (e for e in entries if e.unique_id.endswith(f"_{expose}_zigbee2mqtt")), None
            )
            if entity is not None:
                self._remember(tid, entity.entity_id)
                await self._async_set_state(entity.entity_id, value)

    async def _async_write_number(self, tid: str, entity_id: str, value: float) -> None:
        self._remember(tid, entity_id)
        await self._async_call("number", "set_value", entity_id, value=value)

    def _remember(self, tid: str, entity_id: str) -> None:
        original = self._hass.states.get(entity_id)
        if original is None or original.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        self.restore.setdefault(tid, {}).setdefault(entity_id, original.state)
        self._hass.async_create_task(self._runtime.async_save())

    async def _async_restore(self, tid: str) -> None:
        for entity_id, value in self.restore.pop(tid, {}).items():
            await self._async_set_state(entity_id, value)
        control = self.thermostats.get(tid)
        if control is not None:
            self.thermostats[tid] = ThermostatControl()

    async def _async_set_state(self, entity_id: str, value: str) -> None:
        domain = entity_id.split(".", 1)[0]
        if domain == "number":
            await self._async_call("number", "set_value", entity_id, value=float(value))
        elif domain == "select":
            await self._async_call("select", "select_option", entity_id, option=value)
        elif domain in ("switch", "lock"):
            service = "turn_on" if value == "on" else "turn_off"
            await self._async_call(domain, service, entity_id)

    # ----- giving up (ACT-043) ------------------------------------------------------------

    async def _async_give_up(self, room_id: str, tid: str, thermostat: Thermostat) -> None:
        room_name = self._rooms[room_id].room.name
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            f"device_overrides_valve_{tid}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="device_overrides_valve",
            translation_placeholders={"thermostat": thermostat.name, "room": room_name},
            learn_more_url=f"{self._runtime.docs_url}/en/faq/device_overrides_valve.md",
        )
        await self._async_logbook(
            room_name, "logbook_device_overrides_valve", thermostat=thermostat.name
        )
        await self.async_set_enabled(room_id, False)

    # ----- manual operation on the device (OVR-001) --------------------------------------

    @callback
    def _on_device_climate(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        for tid, thermostat in self._runtime.thermostats.items():
            if thermostat.roles.get(Role.CLIMATE) != entity_id:
                continue
            control = self.thermostats[tid]
            if not self.is_enabled(thermostat.room_id) or control.last_setpoint_c is None:
                continue
            value = self._climate_setpoint(entity_id)
            if value is None or abs(value - control.last_setpoint_c) <= SETPOINT_TOLERANCE_K:
                continue
            if control.pending_override is not None:
                control.pending_override()

            @callback
            def _adopt(_now: datetime, tid: str = tid) -> None:
                self._hass.async_create_task(self._async_adopt(tid))

            control.pending_override = async_call_later(self._hass, OVERRIDE_DEBOUNCE_S, _adopt)

    async def _async_adopt(self, tid: str) -> None:
        thermostat = self._runtime.thermostats[tid]
        control = self.thermostats[tid]
        control.pending_override = None
        value = self._climate_setpoint(thermostat.roles[Role.CLIMATE])
        if value is None or control.last_setpoint_c is None:
            return
        if abs(value - control.last_setpoint_c) <= SETPOINT_TOLERANCE_K:
            return
        control.last_setpoint_c = value
        room_name = self._rooms[thermostat.room_id].room.name
        await self._async_logbook(
            room_name, "logbook_manual_setpoint", thermostat=thermostat.name, setpoint=value
        )
        await self._runtime.async_set_room_setpoint(thermostat.room_id, value)

    # ----- helpers ------------------------------------------------------------------------

    async def _async_call(self, domain: str, service: str, entity_id: str, **data: Any) -> None:
        await self._hass.services.async_call(
            domain, service, {"entity_id": entity_id, **data}, blocking=True
        )

    async def _async_logbook(self, name: str, key: str, **placeholders: Any) -> None:
        language = self._hass.config.language
        translations = await async_get_translations(self._hass, language, "exceptions", {DOMAIN})
        template = translations.get(f"component.{DOMAIN}.exceptions.{key}.message", key)
        self._hass.bus.async_fire(
            LOGBOOK_EVENT,
            {"name": name, "message": template.format(**placeholders), "domain": DOMAIN},
        )

    def _number(self, entity_id: str) -> float | None:
        state = self._hass.states.get(entity_id)
        if state is None:
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _climate_setpoint(self, entity_id: str) -> float | None:
        state = self._hass.states.get(entity_id)
        if state is None:
            return None
        value = state.attributes.get(ATTR_TEMPERATURE)
        return float(value) if value is not None else None
