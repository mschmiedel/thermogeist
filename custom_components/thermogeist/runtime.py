# SPDX-License-Identifier: MIT
"""Runtime state of one house: stored settings, central mode, room decisions and plans.

This is HA glue: it collects inputs from Home Assistant, asks the core for decisions and
tells the entities to refresh. The decisions themselves are made in ``core``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store

from .const import DOCS_URL, DOMAIN, ROOM_SETPOINT_DEFAULT_C, STORAGE_VERSION
from .control import ControlManager
from .core.actuator import DeviceProfile, Thermostat
from .core.controller import (
    ControllerInputs,
    ControllerResult,
    ControllerSettings,
    RoomController,
    feed_forward_pct,
)
from .core.decisions import Decision, ReasonCode, RoomInputs, decide_room
from .core.estimation import ShareResult, room_shares
from .core.heat import current_demand_w, room_heat_loss_w_per_k
from .core.house import CentralMode, House
from .core.profiles import (
    ControlSetting,
    EffectiveSetting,
    effective_settings,
    is_valid_override,
)
from .core.radiator import time_constant_h
from .core.room import Room
from .core.time_provider import SystemTimeProvider, TimeProvider

REEVALUATE_EVERY = timedelta(minutes=1)
# ACT-045: devices need a moment after a restart before Thermogeist writes to them.
STARTUP_HOLD = timedelta(seconds=90)
WINDOW_RECHECK_S = 31


def update_signal(entry_id: str) -> str:
    """Dispatcher signal sent whenever anything of this house changed."""
    return f"{DOMAIN}_{entry_id}_updated"


@dataclass(slots=True)
class RoomState:
    """Live values of one room."""

    room: Room
    user_setpoint_c: float
    share_pct: float
    heat_loss_w_per_k: float | None
    temperature_valid_since: datetime | None = None
    current_temperature_c: float | None = None
    decision: Decision | None = None
    demand_w: float | None = None
    thermostat_ids: list[str] = field(default_factory=list)
    controller: RoomController = field(default_factory=RoomController)
    plan: ControllerResult | None = None
    """Planned valve position (observe mode, ACT-014)."""
    rated_output_w: float | None = None
    """Sum of the known radiator outputs of this room, None if none is known."""
    feed_forward_missing: list[str] = field(default_factory=list)
    """Inputs the feed-forward is waiting for (CTL-035)."""


class HouseRuntime:
    """Everything that changes while Home Assistant runs."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        house: House,
        rooms: dict[str, Room],
        thermostats: dict[str, Thermostat] | None = None,
        clock: TimeProvider | None = None,
        profiles: list[DeviceProfile] | None = None,
    ) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self._clock = clock or SystemTimeProvider()
        self._unsubscribe: list[CALLBACK_TYPE] = []
        self.house_device_id: str | None = None
        self._started = False
        self.house = house
        self.central_mode = CentralMode.AUTO
        self.overrides: dict[ControlSetting, float] = {}
        self.shares: ShareResult = room_shares(house, rooms)
        self.rooms: dict[str, RoomState] = {
            room_id: RoomState(
                room=room,
                user_setpoint_c=ROOM_SETPOINT_DEFAULT_C,
                share_pct=self.shares.shares_pct.get(room_id, 0.0),
                heat_loss_w_per_k=room_heat_loss_w_per_k(
                    house, room, self.shares.shares_pct.get(room_id, 0.0)
                ),
            )
            for room_id, room in rooms.items()
        }
        self.thermostats: dict[str, Thermostat] = thermostats or {}
        for thermostat_id, thermostat in self.thermostats.items():
            if thermostat.room_id in self.rooms:
                self.rooms[thermostat.room_id].thermostat_ids.append(thermostat_id)
        for state in self.rooms.values():
            outputs = [
                self.thermostats[t].rated_output_w
                for t in state.thermostat_ids
                if self.thermostats[t].rated_output_w
            ]
            state.rated_output_w = sum(outputs) if outputs else None
        self.started_at: datetime | None = None
        self.docs_url = DOCS_URL
        self.control = ControlManager(hass, self, profiles or [])

    # ----- lifecycle -------------------------------------------------------------------------

    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.overrides = {
            ControlSetting(key): float(value)
            for key, value in stored.get("overrides", {}).items()
            if key in {setting.value for setting in ControlSetting}
        }
        for room_id, setpoint in stored.get("setpoints", {}).items():
            if room_id in self.rooms:
                self.rooms[room_id].user_setpoint_c = float(setpoint)
        self.control.load(stored)

    @callback
    def async_start(self) -> None:
        # Plans are only computed from here on: before, room temperatures are not read yet and
        # the controller would start from a false safe state (seen when restoring central mode).
        self._started = True
        now = self._clock.now()
        self.started_at = now
        for state in self.rooms.values():
            self._read_temperature(state, now, initial=True)
        watched = [s.room.temperature_entity for s in self.rooms.values()]
        watched += [w for s in self.rooms.values() for w in s.room.window_entities]
        watched.append(self.house.outdoor_temperature_entity)
        if self.house.flow_temperature_entity:
            watched.append(self.house.flow_temperature_entity)
        self._unsubscribe.append(
            async_track_state_change_event(self._hass, watched, self._on_state_change)
        )
        self._unsubscribe.append(
            async_track_time_interval(self._hass, self._on_interval, REEVALUATE_EVERY)
        )
        self._unsubscribe += self.control.async_start()
        self._unsubscribe.append(
            async_call_later(self._hass, STARTUP_HOLD.total_seconds() + 1, self._on_delayed)
        )
        # Devices of thermostats that were removed while controlled get their settings back.
        for orphan in [tid for tid in self.control.restore if tid not in self.thermostats]:
            self._hass.async_create_task(self.control.async_restore_orphan(orphan))
        self._reevaluate()

    @callback
    def async_stop(self) -> None:
        while self._unsubscribe:
            self._unsubscribe.pop()()

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def now(self) -> datetime:
        return self._clock.now()

    def startup_hold(self) -> bool:
        return self.started_at is None or self.now() - self.started_at < STARTUP_HOLD

    @callback
    def reevaluate(self) -> None:
        self._reevaluate()

    @callback
    def _on_delayed(self, _now: datetime) -> None:
        """Delayed re-check (startup hold, window delay); must run in the event loop."""
        self._reevaluate()

    async def async_save(self) -> None:
        await self._save()

    # ----- settings --------------------------------------------------------------------------

    def settings(self) -> dict[ControlSetting, EffectiveSetting]:
        return effective_settings(self.house.heating_type, self.overrides)

    async def async_set_override(self, setting: ControlSetting, value: float) -> None:
        if not is_valid_override(setting, value):
            raise ValueError(f"{setting} out of range: {value}")
        self.overrides[setting] = value
        await self._save()
        self._reevaluate()

    async def async_reset_overrides(self) -> None:
        self.overrides.clear()
        await self._save()
        self._reevaluate()

    @callback
    def set_central_mode(self, mode: CentralMode) -> None:
        self.central_mode = mode
        self._reevaluate()

    async def async_set_room_setpoint(self, room_id: str, setpoint_c: float) -> None:
        self.rooms[room_id].user_setpoint_c = setpoint_c
        await self._save()
        self._reevaluate()

    def outdoor_temperature_c(self) -> float | None:
        return numeric_state(self._hass, self.house.outdoor_temperature_entity)

    def flow_temperature_c(self) -> float | None:
        if not self.house.flow_temperature_entity:
            return None
        return numeric_state(self._hass, self.house.flow_temperature_entity)

    def controller_settings(self) -> ControllerSettings:
        values = self.settings()
        return ControllerSettings(
            min_opening_pct=values[ControlSetting.MIN_VALVE_OPENING].value,
            dead_band_k=values[ControlSetting.DEAD_BAND].value,
            max_change_pct_per_30min=values[ControlSetting.MAX_VALVE_CHANGE].value,
        )

    # ----- evaluation ------------------------------------------------------------------------

    @callback
    def _on_state_change(self, event: Event[EventStateChangedData]) -> None:
        now = self._clock.now()
        new_state = event.data["new_state"]
        if (
            new_state is not None
            and new_state.state == "on"
            and any(event.data["entity_id"] in s.room.window_entities for s in self.rooms.values())
        ):
            # Check again once the 30 s window delay has passed (RUL-010).
            async_call_later(self._hass, WINDOW_RECHECK_S, self._on_delayed)
        for state in self.rooms.values():
            if state.room.temperature_entity == event.data["entity_id"]:
                self._read_temperature(state, now)
        self._reevaluate()

    @callback
    def _on_interval(self, _now: datetime) -> None:
        now = self._clock.now()
        for state in self.rooms.values():
            self._read_temperature(state, now)
        self._reevaluate()

    def _read_temperature(self, state: RoomState, now: datetime, *, initial: bool = False) -> None:
        ha_state = self._hass.states.get(state.room.temperature_entity)
        value = numeric_state(self._hass, state.room.temperature_entity)
        state.current_temperature_c = value
        if value is not None and ha_state is not None:
            state.temperature_valid_since = ha_state.last_reported
        elif initial:
            # Give a sensor that is still starting up the full grace period.
            state.temperature_valid_since = now

    @callback
    def _reevaluate(self) -> None:
        if not self._started:
            # Before start-up the room temperatures are not read yet: deciding now would show a
            # false "sensor silent" in the logbook and start the controller from a false state.
            return
        outdoor = self.outdoor_temperature_c()
        flow = self.flow_temperature_c()
        settings = self.controller_settings()
        for room_id, state in self.rooms.items():
            state.decision = decide_room(
                RoomInputs(
                    user_setpoint_c=state.user_setpoint_c,
                    central_mode=self.central_mode,
                    temperature_valid_since=state.temperature_valid_since,
                    window_open_since=self._window_open_since(state),
                    startup_hold=self.startup_hold() and self.control.is_enabled(room_id),
                ),
                self._clock,
            )
            state.demand_w = current_demand_w(
                state.heat_loss_w_per_k, state.decision.target_setpoint_c, outdoor
            )
            if state.thermostat_ids:
                self._plan(state, flow, settings)
            self._update_sensor_issue(room_id, state)
        self._notify()
        if not self.startup_hold():
            self.control.schedule_apply()

    def _window_open_since(self, state: RoomState) -> datetime | None:
        opened = [
            s.last_changed
            for entity in state.room.window_entities
            if (s := self._hass.states.get(entity)) is not None and s.state == "on"
        ]
        return min(opened) if opened else None

    def _update_sensor_issue(self, room_id: str, state: RoomState) -> None:
        """RSN-004: a silent room sensor shows up under Settings > Repairs."""
        issue_id = f"sensor_stale_{room_id}"
        if state.decision is not None and state.decision.code is ReasonCode.SAFETY_SENSOR_STALE:
            ir.async_create_issue(
                self._hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="sensor_stale",
                translation_placeholders={
                    "room": state.room.name,
                    "sensor": state.room.temperature_entity,
                },
                learn_more_url=f"{DOCS_URL}/en/faq/safety_sensor_stale.md",
            )
        else:
            ir.async_delete_issue(self._hass, DOMAIN, issue_id)

    def _plan(self, state: RoomState, flow: float | None, settings: ControllerSettings) -> None:
        """Observe mode: compute what the valves would do, write nothing (ACT-014)."""
        assert state.decision is not None
        state.feed_forward_missing = [
            name
            for name, value in (
                ("heat_load", state.heat_loss_w_per_k),
                ("radiator_output", state.rated_output_w),
                ("flow_temperature", flow),
                ("room_temperature", state.current_temperature_c),
            )
            if value is None
        ]
        state.plan = state.controller.step(
            ControllerInputs(
                target_c=state.decision.target_setpoint_c,
                room_c=state.current_temperature_c,
                feed_forward_pct=feed_forward_pct(
                    state.demand_w, state.rated_output_w, flow, state.current_temperature_c
                ),
                time_constant_h=time_constant_h(state.room.floor_area_m2, state.heat_loss_w_per_k),
                safety=state.decision.code is ReasonCode.SAFETY_SENSOR_STALE,
                settings=settings,
                window_open=state.decision.code is ReasonCode.WINDOW_OPEN,
            ),
            self._clock.now(),
        )

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self._hass, update_signal(self._entry_id))

    async def _save(self) -> None:
        await self._store.async_save(
            {
                "overrides": {key.value: value for key, value in self.overrides.items()},
                "setpoints": {rid: s.user_setpoint_c for rid, s in self.rooms.items()},
                **self.control.dump(),
            }
        )


def numeric_state(hass: HomeAssistant, entity_id: str) -> float | None:
    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    try:
        return float(state.state)
    except ValueError:
        return None
