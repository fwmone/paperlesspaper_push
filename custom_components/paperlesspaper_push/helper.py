import asyncio
import logging
import os
import random
import shutil
from collections import deque
from datetime import datetime

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def calc_recent_max(n_files: int) -> int:
    # 50% of files, minimum 5, maximum 50
    return max(5, min(50, int(round(n_files * 0.5))))


def guess_mime_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".png":
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"

async def async_list_images(hass: HomeAssistant, input_dir: str) -> list[str]:
    """List images without blocking the event loop."""
    return await hass.async_add_executor_job(_list_images_sync, input_dir)


def _list_images_sync(input_dir: str) -> list[str]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    try:
        entries = os.listdir(input_dir)
    except FileNotFoundError:
        return []
    files: list[str] = []
    for f in entries:
        p = os.path.join(input_dir, f)
        if os.path.isfile(p) and os.path.splitext(f)[1].lower() in exts:
            files.append(f)
    files.sort()
    return files

async def choose_varied(hass: HomeAssistant, files: list[str], store_key: str = "recent") -> str:
    """Choose a file with a moving 'recent' window persisted in Store."""
    recent_max = calc_recent_max(len(files))

    store = hass.data[DOMAIN]["store_recent"]
    data = await store.async_load() or {}
    recent = deque(data.get(store_key, data.get("recent", [])), maxlen=recent_max)

    files_set = set(files)
    recent = deque([f for f in recent if f in files_set], maxlen=recent_max)

    recent_set = set(recent)
    candidates = [f for f in files if f not in recent_set]
    chosen = random.choice(candidates or files)

    recent.append(chosen)
    await store.async_save({"recent": list(recent)})

    return chosen


async def async_publish_copy(hass: HomeAssistant, src_path: str, publish_dir: str) -> str:
    """Copy chosen image to /config/www/... without blocking the event loop."""
    return await hass.async_add_executor_job(_publish_copy_sync, src_path, publish_dir)


def _publish_copy_sync(src_path: str, publish_dir: str) -> str:
    os.makedirs(publish_dir, exist_ok=True)
    base = os.path.basename(src_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_name = f"chosen_{ts}_{base}"
    dst_path = os.path.join(publish_dir, dst_name)
    shutil.copy2(src_path, dst_path)
    return dst_name

def clear_publish_dir_sync(path: str) -> None:
    """Remove all files in publish_dir (non-recursive)."""
    if not os.path.isdir(path):
        return

    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        if os.path.isfile(file_path):
            os.remove(file_path)


async def async_clear_publish_dir(hass: HomeAssistant, path: str) -> None:
    """Async wrapper to avoid blocking the event loop."""
    await hass.async_add_executor_job(clear_publish_dir_sync, path)



async def upload_with_retries(
    hass: HomeAssistant,
    url: str,
    api_key: str,
    file_path: str,
    content_type: str,
    timeout_s: int = 30,
    max_attempts: int = 4,
) -> dict:
    """Upload file as multipart/form-data (field 'picture') with retries/backoff."""
    session = async_get_clientsession(hass)

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            form = aiohttp.FormData()

            # Open file in binary mode for each attempt
            file_bytes = await hass.async_add_executor_job(_read_file_bytes, file_path)

            form.add_field(
                "picture",
                file_bytes,
                filename=os.path.basename(file_path),
                content_type=content_type,
            )

            headers = {"x-api-key": api_key}
            timeout = aiohttp.ClientTimeout(total=timeout_s)

            async with session.post(url, data=form, headers=headers, timeout=timeout) as resp:
                body = await resp.text()

                if 200 <= resp.status < 300:
                    return {"ok": True, "status": resp.status, "body": body}

                # Hard fail: do not retry
                if resp.status in (400, 401, 403, 404):
                    return {
                        "ok": False,
                        "status": resp.status,
                        "body": body[:5000],
                        "error": f"HTTP {resp.status} (non-retryable)",
                    }

                # Retryable: 429 or 5xx
                if resp.status == 429 or 500 <= resp.status < 600:
                    raise aiohttp.ClientResponseError(
                        request_info=resp.request_info,
                        history=resp.history,
                        status=resp.status,
                        message=body[:5000],
                        headers=resp.headers,
                    )

                # Everything else: retry conservatively
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=body[:5000],
                    headers=resp.headers,
                )

        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            last_error = repr(e)
            _LOGGER.warning("Upload attempt %s/%s failed: %s", attempt, max_attempts, e)

            if attempt >= max_attempts:
                break

            # Exponential-ish backoff with jitter, capped
            backoff = min(60.0, (2 ** attempt)) + random.random()
            await asyncio.sleep(backoff)

    return {"ok": False, "status": None, "error": last_error}

def _read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()
