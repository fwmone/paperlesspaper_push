import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.components.sensor import SensorDeviceClass

from .const import (
    DOMAIN,
    ATTR_CURRENT_FILENAME,
    ATTR_LAST_RESULT,
    ATTR_LAST_HTTP_STATUS,
    ATTR_LAST_ERROR,
)

_LOGGER = logging.getLogger(__name__)

DISPATCHER_SIGNAL = f"{DOMAIN}_update"


async def async_setup_sensors(hass: HomeAssistant) -> None:
    """Load the sensor platform via discovery (legacy YAML-style)."""
    # async_load_platform signature: (hass, platform, domain, discovered, hass_config)
    await async_load_platform(hass, "sensor", DOMAIN, {}, hass.config)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = [PaperlesspaperPushStatusSensor(hass)]

    coordinator = hass.data.get(DOMAIN, {}).get("device_coordinator")
    unique_prefix = hass.data.get(DOMAIN, {}).get("device_unique_prefix")

    if coordinator and unique_prefix:
        from .device_sensors import PaperlesspaperDeviceSensor, SENSORS
        entities.extend(PaperlesspaperDeviceSensor(coordinator, sdef, unique_prefix) for sdef in SENSORS)

    async_add_entities(entities, update_before_add=True)


class PaperlesspaperPushStatusSensor(Entity):
    _attr_has_entity_name = True
    _attr_name = "Paperlesspaper Push Status"
    _attr_unique_id = f"{DOMAIN}_status"
    _attr_device_class = SensorDeviceClass.TIMESTAMP    

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._state = None
        self._attrs = {}

        # Provide a callable for __init__.py to notify updates
        hass.data[DOMAIN]["dispatcher_update"] = self._dispatch_update

        self._unsub = None

    async def async_added_to_hass(self):
        self._unsub = async_dispatcher_connect(self.hass, DISPATCHER_SIGNAL, self._handle_update)
        await self._handle_update()

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _dispatch_update(self):
        from homeassistant.helpers.dispatcher import dispatcher_send
        dispatcher_send(self.hass, DISPATCHER_SIGNAL)

    async def _handle_update(self):
        data = self.hass.data.get(DOMAIN, {}).get("state", {}) or {}
        self._state = data.get("last_upload")

        self._attrs = {
            ATTR_CURRENT_FILENAME: data.get(ATTR_CURRENT_FILENAME),
            ATTR_LAST_RESULT: data.get(ATTR_LAST_RESULT),
            ATTR_LAST_HTTP_STATUS: data.get(ATTR_LAST_HTTP_STATUS),
            ATTR_LAST_ERROR: data.get(ATTR_LAST_ERROR),
            "published_name": data.get("published_name"),
        }

        self.async_write_ha_state()

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs
