# SPDX-License-Identifier: MIT
"""Smart child lock: HA glue for ``core.child_lock`` (spec OVR-022 to OVR-024).

Works in observe mode too: the room switch is an explicit wish of the user.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.actuator import Role
from .core.child_lock import Change, LockState, RoomChildLock

if TYPE_CHECKING:
    from homeassistant.core import State

    from .runtime import HouseRuntime

_LOCKED = frozenset({"on", "locked", "lock"})
_UNLOCKED = frozenset({"off", "unlocked", "unlock"})
CHECK_EVERY = timedelta(minutes=1)
"""OVR-023: the unlock time is checked every minute."""
_LOGBOOK = {
    Change.ADOPTED: "logbook_child_lock_adopted",
    Change.PAUSE_ENDED: "logbook_child_lock_pause_ended",
    Change.RESET: "logbook_child_lock_reset",
}


def lock_state(state: State | None) -> LockState:
    """Read a child lock from a switch, lock or select entity."""
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return LockState.UNKNOWN
    value = state.state.lower()
    if value in _LOCKED:
        return LockState.LOCKED
    if value in _UNLOCKED:
        return LockState.UNLOCKED
    return LockState.UNKNOWN


class ChildLockManager:
    """Keeps the child lock of every room the way the room switch says."""

    def __init__(self, hass: HomeAssistant, runtime: HouseRuntime) -> None:
        self._hass = hass
        self._runtime = runtime
        self.rooms: dict[str, RoomChildLock] = {
            room_id: RoomChildLock() for room_id in runtime.rooms if self.entities(room_id)
        }
        self._written_at: dict[str, datetime] = {}

    # ----- state --------------------------------------------------------------------------

    def entities(self, room_id: str) -> dict[str, str]:
        """Lock entity → thermostat name, for the room's thermostats with a child lock."""
        found = {}
        for tid in self._runtime.rooms[room_id].thermostat_ids:
            thermostat = self._runtime.thermostats[tid]
            if entity := thermostat.roles.get(Role.CHILD_LOCK):
                found[entity] = thermostat.name
        return found

    def load(self, stored: dict[str, Any]) -> None:
        for room_id, values in stored.get("child_lock", {}).items():
            if room_id not in self.rooms:
                continue
            until = values.get("until")
            self.rooms[room_id] = RoomChildLock(
                wanted=values.get("on"),
                unlocked_until=datetime.fromisoformat(until) if until else None,
            )

    def dump(self) -> dict[str, Any]:
        return {
            "child_lock": {
                room_id: {
                    "on": lock.wanted,
                    "until": lock.unlocked_until.isoformat() if lock.unlocked_until else None,
                }
                for room_id, lock in self.rooms.items()
            }
        }

    def is_on(self, room_id: str) -> bool:
        return self.rooms[room_id].on

    def unlocked_until(self, room_id: str) -> datetime | None:
        lock = self.rooms[room_id]
        return lock.unlocked_until if lock.paused(self._runtime.now()) else None

    def available(self, room_id: str) -> bool:
        return any(
            lock_state(self._hass.states.get(e)) is not LockState.UNKNOWN
            for e in self.entities(room_id)
        )

    # ----- lifecycle ----------------------------------------------------------------------

    @callback
    def async_start(self) -> list[CALLBACK_TYPE]:
        watched = [e for room_id in self.rooms for e in self.entities(room_id)]
        if not watched:
            return []
        self._hass.async_create_task(self._async_check_all())
        return [
            async_track_state_change_event(self._hass, watched, self._on_lock_change),
            async_track_time_interval(self._hass, self._on_interval, CHECK_EVERY),
        ]

    # ----- user actions -------------------------------------------------------------------

    async def async_set(self, room_id: str, on: bool) -> None:
        """OVR-022: the room switch; off unlocks the devices, on locks them."""
        self.rooms[room_id].set(on)
        if not on:
            await self._async_write_all(room_id, locked=False)
        await self._async_apply(room_id)
        await self._async_changed()

    async def async_unlock_for_a_while(self, room_id: str) -> None:
        """OVR-023: unlock all thermostats of the room until the unlock time is over."""
        lock = self.rooms[room_id]
        if not lock.on:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="child_lock_off")
        until = lock.unlock_for_a_while(self._runtime.now())
        await self._async_write_all(room_id, locked=False)
        await self._logbook(
            room_id, "logbook_child_lock_unlocked", until=dt_util.as_local(until).strftime("%H:%M")
        )
        await self._async_changed()

    # ----- device changes and the clock ---------------------------------------------------

    @callback
    def _on_lock_change(self, event: Event[EventStateChangedData]) -> None:
        self._hass.async_create_task(self._async_lock_change(event))

    async def _async_lock_change(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        room_id = next((r for r in self.rooms if entity_id in self.entities(r)), None)
        if room_id is None:
            return
        lock = self.rooms[room_id]
        if self._first_seen(room_id):
            await self._async_apply(room_id)
            await self._async_changed()
            return
        change = lock.device_changed(
            lock_state(event.data["old_state"]),
            lock_state(event.data["new_state"]),
            self._runtime.now(),
        )
        if change is Change.NONE:
            return
        await self._logbook(room_id, _LOGBOOK[change], thermostat=self.entities(room_id)[entity_id])
        await self._async_apply(room_id)
        await self._async_changed()

    @callback
    def _on_interval(self, _now: datetime) -> None:
        self._hass.async_create_task(self._async_check_all())

    async def _async_check_all(self) -> None:
        now = self._runtime.now()
        changed = False
        for room_id, lock in self.rooms.items():
            if lock.expire(now):
                changed = True
                await self._logbook(room_id, "logbook_child_lock_relocked")
            changed = self._first_seen(room_id) or changed
            await self._async_apply(room_id)
        if changed:
            await self._async_changed()

    def _first_seen(self, room_id: str) -> bool:
        states = [lock_state(self._hass.states.get(e)) for e in self.entities(room_id)]
        return self.rooms[room_id].first_seen(states)

    # ----- writing ------------------------------------------------------------------------

    async def _async_apply(self, room_id: str) -> None:
        lock = self.rooms[room_id]
        now = self._runtime.now()
        for entity_id in self.entities(room_id):
            state = self._hass.states.get(entity_id)
            written = self._written_at.get(entity_id)
            changed = state is not None and written is not None and state.last_changed > written
            if lock.should_lock(lock_state(state), now, written, changed_since_write=changed):
                await self._async_write(entity_id, locked=True)

    async def _async_write_all(self, room_id: str, *, locked: bool) -> None:
        wanted = LockState.LOCKED if locked else LockState.UNLOCKED
        for entity_id in self.entities(room_id):
            current = lock_state(self._hass.states.get(entity_id))
            if current is not LockState.UNKNOWN and current is not wanted:
                await self._async_write(entity_id, locked=locked)

    async def _async_write(self, entity_id: str, *, locked: bool) -> None:
        self._written_at[entity_id] = self._runtime.now()
        domain = entity_id.split(".", 1)[0]
        if domain == "switch":
            await self._call(domain, "turn_on" if locked else "turn_off", entity_id)
        elif domain == "lock":
            await self._call(domain, "lock" if locked else "unlock", entity_id)
        elif domain == "select" and (option := self._select_option(entity_id, locked)):
            await self._call(domain, "select_option", entity_id, option=option)

    def _select_option(self, entity_id: str, locked: bool) -> str | None:
        state = self._hass.states.get(entity_id)
        options = state.attributes.get("options", []) if state else []
        names = _LOCKED if locked else _UNLOCKED
        return next((o for o in options if str(o).lower() in names), None)

    async def _call(self, domain: str, service: str, entity_id: str, **data: Any) -> None:
        await self._hass.services.async_call(
            domain, service, {"entity_id": entity_id, **data}, blocking=True
        )

    async def _logbook(self, room_id: str, key: str, **placeholders: Any) -> None:
        name = self._runtime.rooms[room_id].room.name
        await self._runtime.control.async_logbook(name, key, **placeholders)

    async def _async_changed(self) -> None:
        await self._runtime.async_save()
        self._runtime.notify()
