# SPDX-License-Identifier: MIT
"""Device definitions published by Zigbee2MQTT (spec ACT-034).

Zigbee2MQTT keeps a retained list of all devices with their exposes on ``<base>/bridge/devices``.
Thermogeist reads it through Home Assistant's MQTT integration, if that is set up, to find the
roles of thermostats it has no profile for.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)

DATA_DEVICES = "thermogeist_z2m_devices"
"""hass.data key: IEEE address (lower case) → Zigbee2MQTT device definition."""
DEVICES_TOPIC = "+/bridge/devices"
"""Any base topic: a renamed Zigbee2MQTT base topic needs no setting."""
IDENTIFIER_PREFIX = "zigbee2mqtt_"
"""Home Assistant device identifiers created by Zigbee2MQTT: ("mqtt", "zigbee2mqtt_<ieee>")."""


async def async_track_devices(hass: HomeAssistant) -> None:
    """Subscribe once per Home Assistant run; without MQTT nothing happens."""
    if DATA_DEVICES in hass.data or "mqtt" not in hass.config.components:
        return
    from homeassistant.components import mqtt

    devices: dict[str, Mapping[str, Any]] = {}
    hass.data[DATA_DEVICES] = devices

    @callback
    def _received(message: Any) -> None:
        try:
            payload = json.loads(message.payload)
        except TypeError, ValueError:
            _LOGGER.debug("Unreadable %s", message.topic)
            return
        for device in payload if isinstance(payload, list) else ():
            ieee = device.get("ieee_address")
            definition = device.get("definition")
            if ieee and definition and device.get("supported", True):
                devices[str(ieee).lower()] = definition

    try:
        await mqtt.async_subscribe(hass, DEVICES_TOPIC, _received)
    except Exception:
        hass.data.pop(DATA_DEVICES, None)
        _LOGGER.debug("Could not subscribe to %s", DEVICES_TOPIC, exc_info=True)


def device_definition(hass: HomeAssistant, device: dr.DeviceEntry) -> Mapping[str, Any] | None:
    """The Zigbee2MQTT definition of a Home Assistant device, if known."""
    devices: Mapping[str, Mapping[str, Any]] = hass.data.get(DATA_DEVICES, {})
    for domain, identifier in device.identifiers:
        if domain == "mqtt" and identifier.startswith(IDENTIFIER_PREFIX):
            return devices.get(identifier.removeprefix(IDENTIFIER_PREFIX).lower())
    return None
