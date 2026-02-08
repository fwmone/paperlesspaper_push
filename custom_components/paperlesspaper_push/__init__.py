import logging
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .coordinator import PaperlesspaperDeviceCoordinator

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_PAPER_ID,
    CONF_BASE_URL,
    CONF_INPUT_DIR,
    CONF_PUBLISH_DIR,
    CONF_TIMEOUT,
    CONF_MAX_ATTEMPTS,
    CONF_PUBLISH,
    CONF_DEVICE_ID, 
    CONF_SCAN_INTERVAL, 
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_INPUT_DIR,
    DEFAULT_PUBLISH_DIR,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_PUBLISH,
    STORE_VERSION,
    STORE_KEY_STATE,
    STORE_KEY_RECENT,
    SERVICE_UPLOAD_RANDOM,
    SERVICE_RESET_RECENT,
    SERVICE_FIELD_FORCE_FILE,
    SERVICE_FIELD_DRY_RUN,
    SERVICE_FIELD_PUBLISH,
    SERVICE_REFRESH_DEVICE,
    ATTR_CURRENT_FILENAME,
    ATTR_LAST_RESULT,
    ATTR_LAST_HTTP_STATUS,
    ATTR_LAST_ERROR,
    STATE_SUCCESS,
    STATE_FAILED,
)

from .helper import (
    async_list_images,
    choose_varied,
    async_publish_copy,
    upload_with_retries,
    guess_mime_type,
    async_clear_publish_dir,
)

from .sensor import async_setup_sensors

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    cfg = config.get(DOMAIN)
    if not cfg:
        return True

    api_key = cfg.get(CONF_API_KEY)
    paper_id = cfg.get(CONF_PAPER_ID)

    if not api_key or not paper_id:
        _LOGGER.error("Missing '%s' or '%s' in configuration.yaml", CONF_API_KEY, CONF_PAPER_ID)
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = {
        CONF_API_KEY: api_key,
        CONF_PAPER_ID: paper_id,
        CONF_BASE_URL: cfg.get(CONF_BASE_URL, DEFAULT_BASE_URL).rstrip("/"),
        CONF_INPUT_DIR: cfg.get(CONF_INPUT_DIR, DEFAULT_INPUT_DIR),
        CONF_PUBLISH_DIR: cfg.get(CONF_PUBLISH_DIR, DEFAULT_PUBLISH_DIR),
        CONF_TIMEOUT: int(cfg.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
        CONF_MAX_ATTEMPTS: int(cfg.get(CONF_MAX_ATTEMPTS, DEFAULT_MAX_ATTEMPTS)),
        CONF_PUBLISH: bool(cfg.get(CONF_PUBLISH, DEFAULT_PUBLISH)),
    }

    device_id = cfg.get(CONF_DEVICE_ID)
    scan_interval = int(cfg.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    if device_id:
        coordinator = PaperlesspaperDeviceCoordinator(
            hass=hass,
            api_key=api_key,
            base_url=hass.data[DOMAIN]["config"][CONF_BASE_URL],
            device_id=device_id,
            scan_interval_s=scan_interval,
        )
        hass.data[DOMAIN]["device_coordinator"] = coordinator
        hass.data[DOMAIN]["device_unique_prefix"] = f"{DOMAIN}_{device_id}"

    # Initial fetch so sensors have values right away (YAML setup, no config entry)
    await coordinator.async_refresh()

    # Stores
    hass.data[DOMAIN]["store_state"] = Store(hass, STORE_VERSION, STORE_KEY_STATE)
    hass.data[DOMAIN]["store_recent"] = Store(hass, STORE_VERSION, STORE_KEY_RECENT)

    # Load persisted state (for sensor restore)
    state_data = await hass.data[DOMAIN]["store_state"].async_load() or {}
    hass.data[DOMAIN]["state"] = state_data

    # Setup sensor platform
    await async_setup_sensors(hass)

    async def _save_state_and_update_sensor(new_state: dict):
        hass.data[DOMAIN]["state"] = new_state
        await hass.data[DOMAIN]["store_state"].async_save(new_state)
        # Notify sensor entity to refresh
        dispatcher = hass.data[DOMAIN].get("dispatcher_update")
        if dispatcher:
            dispatcher()

    async def handle_upload_random(call):
        cfg2 = hass.data[DOMAIN]["config"]
        input_dir = cfg2[CONF_INPUT_DIR]
        publish_dir = cfg2[CONF_PUBLISH_DIR]
        base_url = cfg2[CONF_BASE_URL]
        timeout_s = cfg2[CONF_TIMEOUT]
        max_attempts = cfg2[CONF_MAX_ATTEMPTS]

        dry_run = bool(call.data.get(SERVICE_FIELD_DRY_RUN, False))
        publish = bool(call.data.get(SERVICE_FIELD_PUBLISH, cfg2[CONF_PUBLISH]))

        force_file = call.data.get(SERVICE_FIELD_FORCE_FILE)

        files = await async_list_images(hass, input_dir)
        if not files:
            _LOGGER.warning("No images found in %s", input_dir)
            await _save_state_and_update_sensor({
                "last_upload": hass.data[DOMAIN]["state"].get("last_upload"),
                ATTR_CURRENT_FILENAME: None,
                ATTR_LAST_RESULT: STATE_FAILED,
                ATTR_LAST_HTTP_STATUS: None,
                ATTR_LAST_ERROR: f"No images in {input_dir}",
            })
            return

        if force_file:
            if force_file not in files:
                _LOGGER.error("force_file '%s' not found in %s", force_file, input_dir)
                await _save_state_and_update_sensor({
                    "last_upload": hass.data[DOMAIN]["state"].get("last_upload"),
                    ATTR_CURRENT_FILENAME: None,
                    ATTR_LAST_RESULT: STATE_FAILED,
                    ATTR_LAST_HTTP_STATUS: None,
                    ATTR_LAST_ERROR: f"force_file not found: {force_file}",
                })
                return
            chosen = force_file
        else:
            chosen = await choose_varied(hass, files)

        src_path = f"{input_dir.rstrip('/')}/{chosen}"

        published_name = None
        if publish:
            try:
                await async_clear_publish_dir(hass, publish_dir)
                published_name = await async_publish_copy(hass, src_path, publish_dir)
            except Exception as e:
                _LOGGER.exception("Publish copy failed: %s", e)
                # Continue anyway: publish is helpful, not required.

        if dry_run:
            _LOGGER.info("Dry-run: chosen=%s publish=%s published_name=%s", chosen, publish, published_name)
            await _save_state_and_update_sensor({
                "last_upload": hass.data[DOMAIN]["state"].get("last_upload"),
                ATTR_CURRENT_FILENAME: chosen,
                ATTR_LAST_RESULT: "dry_run",
                ATTR_LAST_HTTP_STATUS: None,
                ATTR_LAST_ERROR: None,
                "published_name": published_name,
            })
            return

        url = f"{base_url}/papers/uploadSingleImage/{paper_id}"

        mime = guess_mime_type(src_path)
        result = await upload_with_retries(
            hass=hass,
            url=url,
            api_key=api_key,
            file_path=src_path,
            content_type=mime,
            timeout_s=timeout_s,
            max_attempts=max_attempts,
        )

        if result.get("ok"):
            _LOGGER.info("Upload succeeded: %s (%s)", chosen, result.get("status"))
            await _save_state_and_update_sensor({
                "last_upload": datetime.now(timezone.utc),
                ATTR_CURRENT_FILENAME: chosen,
                ATTR_LAST_RESULT: STATE_SUCCESS,
                ATTR_LAST_HTTP_STATUS: result.get("status"),
                ATTR_LAST_ERROR: None,
                "published_name": published_name,
            })
        else:
            _LOGGER.error("Upload failed: %s (%s) %s", chosen, result.get("status"), result.get("error") or "")
            await _save_state_and_update_sensor({
                "last_upload": hass.data[DOMAIN]["state"].get("last_upload"),
                ATTR_CURRENT_FILENAME: chosen,
                ATTR_LAST_RESULT: STATE_FAILED,
                ATTR_LAST_HTTP_STATUS: result.get("status"),
                ATTR_LAST_ERROR: result.get("error") or result.get("body"),
                "published_name": published_name,
            })

    async def handle_reset_recent(call):
        await hass.data[DOMAIN]["store_recent"].async_save({"recent": []})
        _LOGGER.info("Recent list reset")
        # Keep state, just notify sensor
        dispatcher = hass.data[DOMAIN].get("dispatcher_update")
        if dispatcher:
            dispatcher()

    async def handle_refresh_device(call):
        coordinator = hass.data.get(DOMAIN, {}).get("device_coordinator")
        if coordinator:
            await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_UPLOAD_RANDOM, handle_upload_random)
    hass.services.async_register(DOMAIN, SERVICE_RESET_RECENT, handle_reset_recent)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_DEVICE, handle_refresh_device)

    return True

