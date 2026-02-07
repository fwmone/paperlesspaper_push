import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PaperlesspaperDeviceCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, api_key: str, base_url: str, device_id: str, scan_interval_s: int):
        self.hass = hass
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._device_id = device_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_device",
            update_interval=timedelta(seconds=scan_interval_s),
        )

    async def _async_update_data(self) -> dict:
        session = async_get_clientsession(self.hass)
        url = f"{self._base_url}/devices/{self._device_id}"
        headers = {"x-api-key": self._api_key}

        try:
            async with session.get(url, headers=headers, timeout=30) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}: {text[:3000]}")
                return await resp.json()
        except Exception as e:
            raise UpdateFailed(str(e)) from e
