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
from .core.actuator import (
    DeviceProfile,
    Kind,
    Role,
    Thermostat,
    derived_valve_pct,
    derives_valve,
    hardware_key,
)
from .core.controller import (
    ControllerInputs,
    ControllerResult,
    ControllerSettings,
    RoomController,
    feed_forward_pct,
)
from .core.decisions import (
    Decision,
    ReasonCode,
    RoomInputs,
    decide_room,
    is_closed_for_window,
    window_may_move_device,
)
from .core.estimation import ShareResult, floor_area_not_in_rooms_m2, room_shares
from .core.heat import (
    current_demand_w,
    effective_factor_pct,
    heat_from_sources_w,
    net_demand_w,
    room_heat_loss_w_per_k,
)
from .core.house import FROST_PROTECTION_SETPOINT_C, CentralMode, HeatingType, House
from .core.output import (
    HouseBalance,
    OutputEstimate,
    RadiatorInput,
    RoomBalanceInput,
    ValveSource,
    estimate_room_output,
    house_balance,
)
from .core.profiles import (
    WINDOW_SETTINGS,
    ControlSetting,
    EffectiveSetting,
    effective_settings,
    is_valid_override,
)
from .core.radiator import time_constant_h, usable_spread_k
from .core.room import Room
from .core.sizing import (
    CurveHour,
    HeatingCurve,
    HourCollector,
    HourResult,
    Sizing,
    SizingInputs,
    SizingResult,
    all_heavily_oversized,
    assess,
    fit_heating_curve,
    full_open_hours_in_window,
    fully_open_in_cold,
    recent_hours,
    with_house_cause,
)
from .core.smoothing import HEAT_SOURCE_WINDOW, MovingAverage, plausible_flow
from .core.time_provider import SystemTimeProvider, TimeProvider

REEVALUATE_EVERY = timedelta(minutes=1)
PLAN_EVERY = timedelta(seconds=55)
# ACT-045: devices need a moment after a restart before Thermogeist writes to them.
STARTUP_HOLD = timedelta(seconds=90)
WINDOW_RECHECK_MARGIN_S = 1
CONTROLLER_SAVE_DELAY_S = 60


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
    reason_since: datetime | None = None
    """When the current reason code started (RSN-002)."""
    plan_at: datetime | None = None
    plan_code: ReasonCode | None = None
    source_averages: dict[str, MovingAverage] = field(default_factory=dict)
    """MDL-040: power of each heat source, averaged over 10 minutes."""
    source_factors: dict[str, float] = field(default_factory=dict)
    """MDL-049: factor in use per heat source (from its factor entity or the fixed value)."""
    heat_from_sources_w: float | None = None
    """MDL-044: heat the devices release into the room (after factors), None without sources."""
    sizing: SizingResult | None = None
    """DIA-012: radiator size, None for rooms without thermostats."""
    full_open_hours: list[datetime] = field(default_factory=list)
    """DIA-015: hours of the last 7 days with the valve fully open in the cold."""


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
        self.created_unique_ids: set[str] = set()
        """HAI-017: entities created in this setup; the rest is removed after setup."""
        self._started = False
        self.house = house
        self.central_mode = CentralMode.AUTO
        self.overrides: dict[ControlSetting, float] = {}
        self.room_overrides: dict[str, dict[ControlSetting, float]] = {}
        """RUL-014: window delays set on a room."""
        self.shares: ShareResult = room_shares(house, rooms)
        self.floor_area_not_in_rooms_m2 = floor_area_not_in_rooms_m2(house, rooms)
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
        self._flow_average = MovingAverage()
        self.flow_used_c: float | None = None
        self._return_average = MovingAverage()
        self.return_used_c: float | None = None
        self.spread_used_k: float | None = None
        self._hour_collector = HourCollector()
        self.curve_hours: list[CurveHour] = []
        """DIA-014: hours while heating ran, last 60 days."""
        self.heating_curve: HeatingCurve | None = None

    # ----- lifecycle -------------------------------------------------------------------------

    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.overrides = {
            ControlSetting(key): float(value)
            for key, value in stored.get("overrides", {}).items()
            if key in {setting.value for setting in ControlSetting}
        }
        known = {setting.value for setting in WINDOW_SETTINGS}
        self.room_overrides = {
            room_id: {ControlSetting(k): float(v) for k, v in values.items() if k in known}
            for room_id, values in stored.get("room_overrides", {}).items()
            if room_id in self.rooms
        }
        if saved_at := stored.get("saved_at"):
            saved = datetime.fromisoformat(saved_at)
            hardware = stored.get("controller_hardware", {})
            for room_id, snapshot in stored.get("controller", {}).items():
                if room_id not in self.rooms:
                    continue
                if room_id in hardware and hardware[room_id] != self._hardware_key(room_id):
                    # CTL-045: other valves; start fresh from the heat demand.
                    continue
                self.rooms[room_id].controller.restore(snapshot, saved, self._clock.now())
        for room_id, setpoint in stored.get("setpoints", {}).items():
            if room_id in self.rooms:
                self.rooms[room_id].user_setpoint_c = float(setpoint)
        self._load_sizing(stored.get("sizing", {}))
        self.control.load(stored)

    def _load_sizing(self, stored: dict[str, Any]) -> None:
        now = self._clock.now()
        self.curve_hours = recent_hours(
            (
                CurveHour(datetime.fromisoformat(hour), float(outdoor), float(flow))
                for hour, outdoor, flow in stored.get("curve", [])
            ),
            now,
        )
        self.heating_curve = fit_heating_curve(self.curve_hours)
        for room_id, hours in stored.get("full_open", {}).items():
            if room_id in self.rooms:
                self.rooms[room_id].full_open_hours = full_open_hours_in_window(
                    (datetime.fromisoformat(h) for h in hours), now
                )

    @callback
    def async_start(self) -> None:
        # Plans are only computed from here on: before, room temperatures are not read yet and
        # the controller would start from a false safe state (seen when restoring central mode).
        self._started = True
        now = self._clock.now()
        self.started_at = now
        for state in self.rooms.values():
            self._read_temperature(state, now, initial=True)
            self._sample_sources(state, now)
        watched = [s.room.temperature_entity for s in self.rooms.values()]
        watched += [w for s in self.rooms.values() for w in s.room.window_entities]
        watched.append(self.house.outdoor_temperature_entity)
        if self.house.flow_temperature_entity:
            watched.append(self.house.flow_temperature_entity)
        if self.house.return_temperature_entity:
            watched.append(self.house.return_temperature_entity)
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
        self._update_sizing()
        self._notify()

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
    def notify(self) -> None:
        self._notify()

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

    def window_setting(self, room_id: str, setting: ControlSetting) -> tuple[float, str]:
        """RUL-014: the room's own value, else the house value; with its source."""
        own = self.room_overrides.get(room_id, {}).get(setting)
        if own is not None:
            return own, "room"
        return self.settings()[setting].value, "house"

    async def async_set_room_override(
        self, room_id: str, setting: ControlSetting, value: float
    ) -> None:
        if not is_valid_override(setting, value):
            raise ValueError(f"{setting} out of range: {value}")
        self.room_overrides.setdefault(room_id, {})[setting] = value
        await self._save()
        self._reevaluate()

    async def async_reset_room_overrides(self, room_id: str) -> None:
        self.room_overrides.pop(room_id, None)
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
        self._update_sizing()
        self._reevaluate()

    def outdoor_temperature_c(self) -> float | None:
        return numeric_state(self._hass, self.house.outdoor_temperature_entity)

    def flow_temperature_c(self) -> float | None:
        """Flow temperature as a 30-minute moving average of plausible values (CTL-038/039)."""
        if not self.house.flow_temperature_entity:
            return None
        now = self._clock.now()
        raw = numeric_state(self._hass, self.house.flow_temperature_entity)
        if plausible_flow(raw):
            assert raw is not None
            self._flow_average.add(now, raw)
        self.flow_used_c = self._flow_average.value(now)
        return self.flow_used_c

    def spread_k(self, flow_c: float | None) -> float | None:
        """MDL-019: measured system spread from the averaged flow and return, or None."""
        if not self.house.return_temperature_entity:
            return None
        now = self._clock.now()
        raw = numeric_state(self._hass, self.house.return_temperature_entity)
        if plausible_flow(raw):
            assert raw is not None
            self._return_average.add(now, raw)
        self.return_used_c = self._return_average.value(now)
        self.spread_used_k = usable_spread_k(flow_c, self.return_used_c)
        return self.spread_used_k

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
        if new_state is not None:
            for room_id, state in self.rooms.items():
                if event.data["entity_id"] in state.room.window_entities:
                    # Check again once the window delays have passed (RUL-014).
                    for setting in WINDOW_SETTINGS:
                        delay = self.window_setting(room_id, setting)[0] + WINDOW_RECHECK_MARGIN_S
                        self._unsubscribe.append(
                            async_call_later(self._hass, delay, self._on_delayed)
                        )
        for state in self.rooms.values():
            if state.room.temperature_entity == event.data["entity_id"]:
                self._read_temperature(state, now)
        self._reevaluate()

    @callback
    def _on_interval(self, _now: datetime) -> None:
        now = self._clock.now()
        for state in self.rooms.values():
            self._read_temperature(state, now)
            self._sample_sources(state, now)
        self._reevaluate()
        self._sample_sizing(now)

    # ----- radiator sizing (DIA-012 to DIA-015) -----------------------------------------------

    def _sample_sizing(self, now: datetime) -> None:
        outdoor = self.outdoor_temperature_c()
        raw_flow = (
            numeric_state(self._hass, self.house.flow_temperature_entity)
            if self.house.flow_temperature_entity
            else None
        )
        rooms = [
            s.current_temperature_c
            for s in self.rooms.values()
            if s.current_temperature_c is not None
        ]
        full_open = {
            room_id: fully_open_in_cold(
                self._sizing_valve_pct(room_id, state),
                state.current_temperature_c,
                state.decision.target_setpoint_c if state.decision else None,
                outdoor,
                state.decision is not None and state.decision.code is ReasonCode.SETPOINT,
            )
            for room_id, state in self.rooms.items()
            if state.thermostat_ids
        }
        finished = self._hour_collector.add(
            now,
            outdoor,
            raw_flow if plausible_flow(raw_flow) else None,
            sum(rooms) / len(rooms) if rooms else None,
            full_open,
        )
        if finished is not None:
            self._close_hour(finished, now)

    def estimated_output(self, room_id: str) -> OutputEstimate:
        """MDL-013: what the room's radiators give right now (estimate)."""
        state = self.rooms[room_id]
        controlled = self.control.is_enabled(room_id) and state.plan is not None
        radiators = []
        for tid in state.thermostat_ids:
            thermostat = self.thermostats[tid]
            valve, source = self.valve_position(tid)
            if valve is None and controlled and thermostat.kind is Kind.VALVE:
                assert state.plan is not None
                valve, source = state.plan.output_pct, ValveSource.PLANNED
            radiators.append(
                RadiatorInput(thermostat.name, thermostat.rated_output_w, valve, source)
            )
        return estimate_room_output(
            radiators, self.flow_used_c, state.current_temperature_c, self.spread_used_k
        )

    def house_balance(self) -> HouseBalance:
        """MDL-052, MDL-053: demand and supply summed over the rooms with an estimate."""
        return house_balance(
            [
                RoomBalanceInput(
                    state.room.name,
                    state.demand_w,
                    self.estimated_output(room_id).output_w if state.thermostat_ids else None,
                    state.heat_from_sources_w,
                )
                for room_id, state in self.rooms.items()
            ]
        )

    def valve_position(self, tid: str) -> tuple[float | None, ValveSource | None]:
        """Where a thermostat's valve is: reported, or derived (ACT-016); None if unknown."""
        thermostat = self.thermostats[tid]
        roles = thermostat.roles
        if (entity := roles.get(Role.VALVE_READ)) is not None:
            value = numeric_state(self._hass, entity)
            return value, ValveSource.REPORTED if value is not None else None
        if not derives_valve(roles):
            return None, None
        climate = self._hass.states.get(roles[Role.CLIMATE])
        value = derived_valve_pct(
            numeric_state(self._hass, roles[Role.VALVE_WRITE]),
            numeric_state(self._hass, roles[Role.VALVE_MIN]),
            closing_inverted=thermostat.valve_min_inverted,
            hvac_action=climate.attributes.get("hvac_action") if climate else None,
        )
        return value, ValveSource.DERIVED if value is not None else None

    def _sizing_valve_pct(self, room_id: str, state: RoomState) -> float | None:
        """DIA-015: the reported or derived valve, else the plan while Thermogeist controls."""
        values = [v for t in state.thermostat_ids if (v := self.valve_position(t)[0]) is not None]
        if values:
            return sum(values) / len(values)
        if self.control.is_enabled(room_id) and state.plan is not None:
            return state.plan.output_pct
        return None

    def _close_hour(self, finished: HourResult, now: datetime) -> None:
        if finished.curve_hour is not None:
            self.curve_hours.append(finished.curve_hour)
        self.curve_hours = recent_hours(self.curve_hours, now)
        self.heating_curve = fit_heating_curve(self.curve_hours)
        for room_id, state in self.rooms.items():
            if room_id in finished.full_open_rooms:
                state.full_open_hours.append(finished.hour)
            state.full_open_hours = full_open_hours_in_window(state.full_open_hours, now)
        self._update_sizing()
        self._save_later()
        self._notify()

    def _update_sizing(self) -> None:
        heat_pump = self.house.heating_type is HeatingType.HEAT_PUMP
        for state in self.rooms.values():
            if not state.thermostat_ids:
                continue
            state.sizing = assess(
                SizingInputs(
                    heat_loss_w_per_k=state.heat_loss_w_per_k,
                    setpoint_c=state.user_setpoint_c,
                    design_outdoor_c=self.house.design_outdoor_temperature_c,
                    rated_output_w=state.rated_output_w,
                    has_flow_sensor=self.house.flow_temperature_entity is not None,
                    curve=self.heating_curve,
                    spread_k=self.spread_used_k,
                    full_open_hours=len(state.full_open_hours),
                    heat_pump=heat_pump,
                )
            )
        results = [s.sizing for s in self.rooms.values() if s.sizing is not None]
        all_oversized = all_heavily_oversized(results)
        if all_oversized:
            for state in self.rooms.values():
                if state.sizing is not None:
                    state.sizing = with_house_cause(state.sizing)
        self._update_sizing_issues(all_oversized, heat_pump)

    def _update_sizing_issues(self, all_oversized: bool, heat_pump: bool) -> None:
        """DIA-013: actionable sizing results under Settings > Repairs."""
        for room_id, state in self.rooms.items():
            sizing = state.sizing.sizing if state.sizing else None
            self._set_issue(
                f"radiator_undersized_{room_id}",
                sizing is Sizing.UNDERSIZED,
                "radiator_undersized",
                {"room": state.room.name},
            )
            self._set_issue(
                f"radiator_oversized_{room_id}",
                sizing is Sizing.HEAVILY_OVERSIZED and not heat_pump,
                "radiator_oversized",
                {"room": state.room.name},
            )
        self._set_issue(
            "flow_higher_than_needed",
            all_oversized,
            "flow_higher_than_needed",
            {"house": self.house.name},
        )

    def _set_issue(
        self, issue_id: str, active: bool, key: str, placeholders: dict[str, str]
    ) -> None:
        if not active:
            ir.async_delete_issue(self._hass, DOMAIN, issue_id)
            return
        ir.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=key,
            translation_placeholders=placeholders,
            learn_more_url=f"{DOCS_URL}/en/faq/radiator_sizing.md",
        )

    def _sample_sources(self, state: RoomState, now: datetime) -> None:
        """MDL-040: one sample per minute; unavailable or negative readings count as 0 W."""
        if not state.room.heat_sources:
            return
        for source in state.room.heat_sources:
            average = state.source_averages.setdefault(
                source.entity_id, MovingAverage(HEAT_SOURCE_WINDOW)
            )
            average.add(now, max(0.0, numeric_state(self._hass, source.entity_id) or 0.0))
            entity_value = (
                numeric_state(self._hass, source.factor_entity) if source.factor_entity else None
            )
            state.source_factors[source.entity_id] = effective_factor_pct(
                entity_value, source.factor_pct
            )
        state.heat_from_sources_w = heat_from_sources_w(
            (state.source_averages[s.entity_id].value(now), state.source_factors[s.entity_id])
            for s in state.room.heat_sources
        )

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
        spread = self.spread_k(flow)
        settings = self.controller_settings()
        for room_id, state in self.rooms.items():
            before = state.decision
            previous = before.code if before else None
            guard_before = before is not None and "frost_guard" in before.params
            state.decision = decide_room(
                RoomInputs(
                    user_setpoint_c=state.user_setpoint_c,
                    central_mode=self.central_mode,
                    temperature_valid_since=state.temperature_valid_since,
                    window_open_since=self._window_open_since(state),
                    startup_hold=self.startup_hold() and self.control.is_enabled(room_id),
                    window_closed_since=self._window_closed_since(state),
                    window_was_active=previous is ReasonCode.WINDOW_OPEN,
                    window_open_after=timedelta(
                        seconds=self.window_setting(room_id, ControlSetting.WINDOW_CLOSE_AFTER)[0]
                    ),
                    window_resume_after=timedelta(
                        seconds=self.window_setting(room_id, ControlSetting.WINDOW_RESUME_AFTER)[0]
                    ),
                    room_temperature_c=state.current_temperature_c,
                    frost_guard_was_active=guard_before,
                ),
                self._clock,
            )
            if state.decision.code != previous:
                state.reason_since = state.decision.timestamp
            if "frost_guard" in state.decision.params and not guard_before:
                self._hass.async_create_task(
                    self.control.async_logbook(
                        state.room.name,
                        "logbook_frost_guard",
                        setpoint=FROST_PROTECTION_SETPOINT_C,
                    )
                )
            state.demand_w = current_demand_w(
                state.heat_loss_w_per_k, state.decision.target_setpoint_c, outdoor
            )
            if state.thermostat_ids:
                self._plan(state, flow, spread, settings)
                self._save_later()
            self._update_sensor_issue(room_id, state)
        self._notify()
        if not self.startup_hold():
            self.control.schedule_apply()

    def _reported_valve_pct(self, state: RoomState) -> float | None:
        """Mean reported valve position of the room's thermostats (CTL-044)."""
        values = []
        for tid in state.thermostat_ids:
            # Only a reported position counts: a write-only setting (Sonoff valve_opening_degree,
            # 100 % from the factory) says nothing about where the valve is.
            entity = self.thermostats[tid].roles.get(Role.VALVE_READ)
            if entity and (value := numeric_state(self._hass, entity)) is not None:
                values.append(value)
        return sum(values) / len(values) if values else None

    def window_may_move_device(self, room_id: str) -> bool:
        """OVR-005: setpoint changes on the device now are likely its own window function."""
        state = self.rooms[room_id]
        return window_may_move_device(
            self._window_open_since(state), self._window_closed_since(state), self.now()
        )

    def _window_closed_since(self, state: RoomState) -> datetime | None:
        """Since when all contacts are closed; None while one is open or without contacts."""
        states = [self._hass.states.get(entity) for entity in state.room.window_entities]
        known = [s for s in states if s is not None]
        if not known or any(s.state == "on" for s in known):
            return None
        return max(s.last_changed for s in known)

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

    def _plan(
        self,
        state: RoomState,
        flow: float | None,
        spread: float | None,
        settings: ControllerSettings,
    ) -> None:
        """Compute what the valves should do (CTL-042: at most once per minute)."""
        assert state.decision is not None
        now = self._clock.now()
        if (
            state.plan is not None
            and state.plan_at is not None
            and state.plan_code is state.decision.code
            and now - state.plan_at < PLAN_EVERY
        ):
            # Sensor noise (e.g. a flow sensor toggling every few seconds) must not recompute
            # and rewrite the plan; a changed reason (window, stop, safety) is applied at once.
            return
        state.plan_at = now
        state.plan_code = state.decision.code
        if state.controller.state.last_output_pct is None:
            actual = self._reported_valve_pct(state)
            if actual is not None:
                state.controller.seed(actual)
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
                    net_demand_w(state.demand_w, state.heat_from_sources_w or 0.0),
                    state.rated_output_w,
                    flow,
                    # CTL-030: the position that holds the room at its target, so the output
                    # is computed at the target, not at a room warmed by sun or devices.
                    state.decision.target_setpoint_c or state.current_temperature_c,
                    spread,
                ),
                time_constant_h=time_constant_h(state.room.floor_area_m2, state.heat_loss_w_per_k),
                safety=state.decision.code is ReasonCode.SAFETY_SENSOR_STALE,
                settings=settings,
                window_open=is_closed_for_window(state.decision),
            ),
            self._clock.now(),
        )

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self._hass, update_signal(self._entry_id))

    async def _save(self) -> None:
        await self._store.async_save(self._data())

    def _hardware_key(self, room_id: str) -> str:
        return hardware_key(self.thermostats[t] for t in self.rooms[room_id].thermostat_ids)

    @callback
    def _save_later(self) -> None:
        """CTL-040: the controller state changes every minute; write it at most that often."""
        self._store.async_delay_save(self._data, CONTROLLER_SAVE_DELAY_S)

    def _data(self) -> dict[str, Any]:
        return {
            "controller": {rid: s.controller.snapshot() for rid, s in self.rooms.items() if s.plan},
            "controller_hardware": {
                rid: self._hardware_key(rid) for rid, s in self.rooms.items() if s.plan
            },
            "saved_at": self._clock.now().isoformat(),
            "overrides": {key.value: value for key, value in self.overrides.items()},
            "room_overrides": {
                rid: {key.value: value for key, value in values.items()}
                for rid, values in self.room_overrides.items()
            },
            "setpoints": {rid: s.user_setpoint_c for rid, s in self.rooms.items()},
            "sizing": {
                "curve": [
                    [h.hour.isoformat(), round(h.outdoor_c, 2), round(h.flow_c, 2)]
                    for h in self.curve_hours
                ],
                "full_open": {
                    rid: [h.isoformat() for h in s.full_open_hours]
                    for rid, s in self.rooms.items()
                    if s.full_open_hours
                },
            },
        } | self.control.dump()


def numeric_state(hass: HomeAssistant, entity_id: str) -> float | None:
    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    try:
        return float(state.state)
    except ValueError:
        return None
