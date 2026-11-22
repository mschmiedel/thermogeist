# SPDX-License-Identifier: MIT
"""Control mode: write plans to thermostats (spec ACT-040 to ACT-054, OVR-001, OVR-004, OVR-005,
RSN-003, RSN-004).

This is HA glue. What to write is decided in ``core`` (controller, decisions, supervision);
this module only talks to the devices, remembers what it changed and puts it back.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import ATTR_TEMPERATURE, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.translation import async_get_translations

from .const import DOMAIN
from .core.actuation import should_write
from .core.actuator import DeviceProfile, Kind, Role, Source, Thermostat
from .core.controller import ControllerResult, Limit
from .core.decisions import ReasonCode, is_closed_for_window
from .core.setpoint import (
    CLOSED_SETPOINT_C,
    device_setpoint_c,
    round_setpoint,
    should_write_setpoint,
)
from .core.smoothing import MovingAverage
from .core.supervision import ValveSupervisor, Verdict

if TYPE_CHECKING:
    from .runtime import HouseRuntime, RoomState

EXTERNAL_TEMPERATURE_REFRESH = timedelta(minutes=20)
"""ACT-041: Bosch falls back to its own sensor after 30 min without a value."""
EXTERNAL_TEMPERATURE_STEP_K = 0.1
SETTING_RETRY_AFTER = timedelta(minutes=10)
"""ACT-049: a device that reported its old value again gets the setting again, this often."""
LOST_EXTERNAL_K = 0.5
"""ACT-049: the device shows something else than the last value sent; send it again."""
OVERRIDE_DEBOUNCE_S = 20
"""OVR-002: wait until the knob has stopped turning."""
STOP_SETPOINT_C = CLOSED_SETPOINT_C
URGENT_CODES = frozenset(
    {ReasonCode.WINDOW_OPEN, ReasonCode.CENTRAL_STOP, ReasonCode.SAFETY_SENSOR_STALE}
)
"""ACT-053: these reasons change a setpoint at once, without bundling."""
SETPOINT_TOLERANCE_K = 0.05
LOGBOOK_EVENT = "logbook_entry"
_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ThermostatControl:
    """What Thermogeist last did with one thermostat."""

    supervisor: ValveSupervisor = field(default_factory=ValveSupervisor)
    last_setpoint_c: float | None = None
    external_value_c: float | None = None
    external_sent_at: datetime | None = None
    settings_applied: bool = False
    settings_written_at: datetime | None = None
    """ACT-049: only a device change after this counts as a reset."""
    pending_override: CALLBACK_TYPE | None = None
    last_write_urgent: bool = False
    """Leaving an urgent state (window closed again) is just as urgent as entering it."""
    last_sent_at: datetime | None = None
    """Last time any valve value was sent, including confirmations (ACT-047)."""
    last_write_at: datetime | None = None
    last_write_pct: float | None = None
    last_confirmation_at: datetime | None = None
    offset_average: MovingAverage = field(default_factory=MovingAverage)
    """ACT-052: device temperature minus room temperature, averaged over 30 minutes."""
    setpoint_offset_k: float = 0.0
    """Difference between the last sent device setpoint and the room target (ACT-052)."""
    setpoint_written_at: datetime | None = None
    resync: bool = False
    """OVR-004/OVR-005: a device setpoint change was ignored; put our value back."""


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
        """ACT-044: every thermostat can be controlled, by valve or by setpoint."""
        return bool(self._rooms[room_id].thermostat_ids)

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
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="no_thermostat")
        self.enabled[room_id] = on
        if on:
            for tid in self._rooms[room_id].thermostat_ids:
                ir.async_delete_issue(self._hass, DOMAIN, f"device_overrides_valve_{tid}")
        else:
            for tid in self._rooms[room_id].thermostat_ids:
                await self._async_restore(tid)
                await self._async_hand_back_setpoint(room_id, tid)
        await self._runtime.async_save()
        self._runtime.reevaluate()

    async def async_restore_orphan(self, tid: str) -> None:
        """Hand a removed thermostat's device back (ACT-008)."""
        await self._async_restore(tid)
        await self._runtime.async_save()

    def write_info(self, tid: str) -> dict[str, Any]:
        """ACT-048: what Thermogeist last did with this thermostat, for its attributes."""
        control = self.thermostats.get(tid)
        if control is None:
            return {}
        if self._runtime.thermostats[tid].kind is Kind.SETPOINT:
            return {
                "last_write": (
                    control.setpoint_written_at.isoformat() if control.setpoint_written_at else None
                ),
                "last_write_value": control.last_setpoint_c,
                "setpoint_offset": round(control.setpoint_offset_k, 1),
            }
        return {
            "last_write": control.last_write_at.isoformat() if control.last_write_at else None,
            "last_write_value": control.last_write_pct,
            "last_confirmation": (
                control.last_confirmation_at.isoformat() if control.last_confirmation_at else None
            ),
            "rewrites_last_hour": control.supervisor.rewrites_last_hour(self._runtime.now()),
        }

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
            control = self.thermostats[tid]
            if not control.settings_applied:
                await self._async_apply_settings(tid, thermostat)
                control.settings_applied = True
                control.settings_written_at = self._runtime.now()
            else:
                await self._async_check_settings(tid, thermostat, control)
            if thermostat.kind is Kind.SETPOINT:
                await self._async_external_temperature(thermostat, control, state)
                await self._async_device_setpoint(thermostat, control, state)
                continue
            if not await self._async_valve(room_id, tid, thermostat, state.plan):
                return
            await self._async_min_opening(tid, thermostat, state.plan)
            await self._async_external_temperature(thermostat, control, state)
            await self._async_setpoint(thermostat, control, target)
        self._runtime.notify()

    async def _async_device_setpoint(
        self, thermostat: Thermostat, control: ThermostatControl, state: RoomState
    ) -> None:
        """ACT-051 to ACT-053: let the device regulate, aiming at the right room temperature."""
        assert state.decision is not None
        entity = thermostat.roles[Role.CLIMATE]
        now = self._runtime.now()
        external = Role.EXTERNAL_TEMPERATURE in thermostat.roles
        room_c = state.current_temperature_c
        device_c = self._climate_temperature(entity)
        if not external and room_c is not None and device_c is not None:
            control.offset_average.add(now, device_c - room_c)
        code = state.decision.code
        target = None if is_closed_for_window(state.decision) else state.decision.target_setpoint_c
        offset = None if external else control.offset_average.value(now)
        desired = device_setpoint_c(
            target,
            room_c,
            None if offset is None or room_c is None else room_c + offset,
            external_input=external,
        )
        self._resync_device_setpoint(thermostat, control, desired)
        if target is not None and await self._async_ensure_heating(thermostat):
            control.last_setpoint_c = None  # ACT-055: write the setpoint again after "off"
        if should_write_setpoint(
            desired,
            control.last_setpoint_c,
            control.setpoint_written_at,
            now,
            urgent=code in URGENT_CODES or control.last_write_urgent,
        ):
            control.last_setpoint_c = desired
            control.setpoint_written_at = now
            control.setpoint_offset_k = 0.0 if target is None else desired - target
            control.last_write_urgent = code in URGENT_CODES
            await self._async_call("climate", "set_temperature", entity, temperature=desired)

    async def _async_ensure_heating(self, thermostat: Thermostat) -> bool:
        """ACT-055: a device switched off (Bosch Smart Home at 5 °C) is set back to heat."""
        entity = thermostat.roles[Role.CLIMATE]
        state = self._hass.states.get(entity)
        if state is None or state.state != "off":
            return False
        if "heat" not in (state.attributes.get("hvac_modes") or []):
            return False
        await self._async_call("climate", "set_hvac_mode", entity, hvac_mode="heat")
        return True

    def _resync_device_setpoint(
        self, thermostat: Thermostat, control: ThermostatControl, desired: float
    ) -> None:
        """OVR-004: an ignored device setpoint is replaced, but not while a window is involved.

        During a window the device's own window function may hold its value; fighting it would
        only move the motor (OVR-005).
        """
        if not control.resync or self._runtime.window_may_move_device(thermostat.room_id):
            return
        control.resync = False
        shown = self._climate_setpoint(thermostat.roles[Role.CLIMATE])
        if shown is not None and abs(shown - desired) > SETPOINT_TOLERANCE_K:
            control.last_setpoint_c = None  # forces the write

    async def _async_valve(
        self, room_id: str, tid: str, thermostat: Thermostat, plan: ControllerResult
    ) -> bool:
        """Write the planned position; returns False if Thermogeist gave up on this room."""
        control = self.thermostats[tid]
        write_entity = thermostat.roles[Role.VALVE_WRITE]
        output_pct = plan.output_pct
        now = self._runtime.now()
        urgent_now = bool({Limit.WINDOW, Limit.STOPPED, Limit.SAFETY} & set(plan.limits))
        urgent = urgent_now or control.last_write_urgent
        supervisor = control.supervisor
        if should_write(
            output_pct, supervisor.last_written_pct, supervisor.last_written_at, now, urgent=urgent
        ):
            await self._async_write_number(tid, write_entity, output_pct)
            supervisor.written(output_pct, now)
            control.last_write_urgent = urgent_now
            control.last_sent_at = now
            control.last_write_at, control.last_write_pct = now, output_pct
            return True
        if self._refresh_due(thermostat, control, now) and supervisor.last_written_pct is not None:
            # Confirm the unchanged value before the device drops it; no motor movement.
            await self._async_call(
                "number", "set_value", write_entity, value=supervisor.last_written_pct
            )
            control.last_sent_at = now
            control.last_confirmation_at = now
            return True
        read_entity = thermostat.roles.get(Role.VALVE_READ, write_entity)
        verdict = supervisor.check(self._number(read_entity), now)
        if verdict is Verdict.REWRITE:
            rewrite = supervisor.last_written_pct
            assert rewrite is not None
            await self._async_write_number(tid, write_entity, rewrite)
            supervisor.written(rewrite, now)
            control.last_write_at, control.last_write_pct = now, rewrite
        elif verdict is Verdict.GIVE_UP:
            await self._async_give_up(room_id, tid, thermostat)
            return False
        return True

    def _refresh_due(
        self, thermostat: Thermostat, control: ThermostatControl, now: datetime
    ) -> bool:
        if thermostat.valve_refresh is None or control.last_sent_at is None:
            return False
        return now - control.last_sent_at >= thermostat.valve_refresh

    async def _async_min_opening(
        self, tid: str, thermostat: Thermostat, plan: ControllerResult
    ) -> None:
        """ACT-102: the device's own minimum; it follows a plan below the minimum opening."""
        entity = thermostat.roles.get(Role.VALVE_MIN)
        if entity is None:
            return
        # The device rests on this position while the room is above its setpoint; a plan below
        # the minimum (too warm, window, stop) must reach the valve in that state too.
        minimum = min(
            self._runtime.controller_settings().min_opening_pct, float(round(plan.output_pct))
        )
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
            or self._external_lost(entity, control)
        )
        due = (
            control.external_sent_at is None
            or now - control.external_sent_at >= EXTERNAL_TEMPERATURE_REFRESH
        )
        if changed or due:
            await self._async_call("number", "set_value", entity, value=value)
            control.external_value_c = value
            control.external_sent_at = now

    def _external_lost(self, entity: str, control: ThermostatControl) -> bool:
        """ACT-049: the device changed the value itself after we sent it (e.g. to 0)."""
        state = self._hass.states.get(entity)
        sent = control.external_value_c
        if state is None or sent is None or control.external_sent_at is None:
            return False
        if state.last_changed <= control.external_sent_at:
            return False
        shown = self._number(entity)
        return shown is not None and abs(shown - sent) > LOST_EXTERNAL_K

    async def _async_setpoint(
        self, thermostat: Thermostat, control: ThermostatControl, target: float | None
    ) -> None:
        """OVR-004: the device display shows the real room target."""
        entity = thermostat.roles[Role.CLIMATE]
        desired = STOP_SETPOINT_C if target is None else target
        if target is not None:
            await self._async_ensure_heating(thermostat)
        if control.resync and not self._runtime.window_may_move_device(thermostat.room_id):
            control.resync = False  # the comparison below puts the value back
        current = self._climate_setpoint(entity)
        if current is None or abs(current - desired) > SETPOINT_TOLERANCE_K:
            control.last_setpoint_c = desired
            await self._async_call("climate", "set_temperature", entity, temperature=desired)
        elif control.last_setpoint_c is None:
            control.last_setpoint_c = desired

    # ----- device settings and restore (ACT-008, ACT-042) ---------------------------------

    def _device_settings(self, thermostat: Thermostat) -> list[tuple[str, str]]:
        """ACT-042: (entity id, value) of the settings the profile needs for control."""
        profile = self._profiles.get(thermostat.profile_id or "")
        if profile is None or thermostat.device_id is None:
            return []
        entries = er.async_entries_for_device(er.async_get(self._hass), thermostat.device_id)
        settings = (
            profile.setpoint_control_settings
            if thermostat.kind is Kind.SETPOINT
            else profile.control_settings
        )
        found = []
        for expose, value in settings.get(Source.Z2M, ()):
            entity = next(
                (e for e in entries if e.unique_id.endswith(f"_{expose}_zigbee2mqtt")), None
            )
            if entity is not None:
                found.append((entity.entity_id, value))
        return found

    async def _async_apply_settings(self, tid: str, thermostat: Thermostat) -> None:
        for entity_id, value in self._device_settings(thermostat):
            self._remember(tid, entity_id)
            await self._async_set_state(entity_id, value)

    async def _async_check_settings(
        self, tid: str, thermostat: Thermostat, control: ThermostatControl
    ) -> None:
        """ACT-049: a firmware update or restart of the device resets its settings."""
        for entity_id, value in self._device_settings(thermostat):
            state = self._hass.states.get(entity_id)
            if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                continue
            if _same_setting(state.state, value):
                continue
            written = control.settings_written_at
            if written is not None and not _write_lost_or_reset(
                state, written, self._runtime.now()
            ):
                continue
            await self._async_set_state(entity_id, value)
            control.settings_written_at = self._runtime.now()
            control.external_value_c = None  # resend the room temperature right away
            room_name = self._rooms[thermostat.room_id].room.name
            await self.async_logbook(
                room_name,
                "logbook_device_setting_reset",
                thermostat=thermostat.name,
                setting=entity_id,
                value=value,
            )

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

    async def _async_hand_back_setpoint(self, room_id: str, tid: str) -> None:
        """ACT-052: a setpoint thermostat gets the plain room setpoint back."""
        thermostat = self._runtime.thermostats[tid]
        if thermostat.kind is not Kind.SETPOINT:
            return
        await self._async_call(
            "climate",
            "set_temperature",
            thermostat.roles[Role.CLIMATE],
            temperature=self._rooms[room_id].user_setpoint_c,
        )

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
        await self.async_logbook(
            room_name, "logbook_device_overrides_valve", thermostat=thermostat.name
        )
        await self.async_set_enabled(room_id, False)

    # ----- manual operation on the device (OVR-001, OVR-004) --------------------------------------

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
                control.pending_override = None
            if thermostat.kind is Kind.SETPOINT:
                # OVR-004: knob, schedule or window function of the device look the same.
                control.resync = True
                _LOGGER.debug("%s: device setpoint %s ignored", thermostat.name, value)
                continue
            if self._ignore_for_window(thermostat, control):
                continue

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
        if self._ignore_for_window(thermostat, control):
            return
        control.last_setpoint_c = value
        room_setpoint = round_setpoint(value)
        room_name = self._rooms[thermostat.room_id].room.name
        await self.async_logbook(
            room_name, "logbook_manual_setpoint", thermostat=thermostat.name, setpoint=room_setpoint
        )
        await self._runtime.async_set_room_setpoint(thermostat.room_id, room_setpoint)

    def _ignore_for_window(self, thermostat: Thermostat, control: ThermostatControl) -> bool:
        """OVR-005: around an open window a changed device setpoint is not a person's wish.

        Devices with their own window function (e.g. Bosch Room Climate Control) lower their
        setpoint themselves; Thermogeist cannot tell that from a turned knob.
        """
        if control.resync or self._runtime.window_may_move_device(thermostat.room_id):
            control.resync = True
            _LOGGER.debug("%s: setpoint change around a window ignored", thermostat.name)
            return True
        return False

    # ----- helpers ------------------------------------------------------------------------

    async def _async_call(self, domain: str, service: str, entity_id: str, **data: Any) -> None:
        await self._hass.services.async_call(
            domain, service, {"entity_id": entity_id, **data}, blocking=True
        )

    async def async_logbook(self, name: str, key: str, **placeholders: Any) -> None:
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

    def _climate_temperature(self, entity_id: str) -> float | None:
        """The device's own temperature reading."""
        state = self._hass.states.get(entity_id)
        value = state.attributes.get("current_temperature") if state else None
        try:
            return float(value) if value is not None else None
        except TypeError, ValueError:
            return None

    def _climate_setpoint(self, entity_id: str) -> float | None:
        state = self._hass.states.get(entity_id)
        if state is None:
            return None
        value = state.attributes.get(ATTR_TEMPERATURE)
        return float(value) if value is not None else None


def _same_setting(current: str, wanted: str) -> bool:
    """Compare a device setting, numbers by value (Home Assistant reports "5.0" for 5)."""
    if current == wanted:
        return True
    try:
        return float(current) == float(wanted)
    except ValueError:
        return False


def _write_lost_or_reset(state: State, written: datetime, now: datetime) -> bool:
    """ACT-049: did the device reset a setting, or report its old value after our write?

    A changed value after our write is a reset (firmware update): set it again at once. The old
    value reported again means our write was lost (e.g. during an update): retry, but at most
    every 10 minutes. A device that reports nothing is never rewritten, to spare its battery.
    """
    if state.last_changed > written:
        return True
    return state.last_reported > written and now - written >= SETTING_RETRY_AFTER
