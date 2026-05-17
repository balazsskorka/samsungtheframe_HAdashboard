"""Samsung Frame Art custom integration."""
from __future__ import annotations

import logging
import os
import random
import json
import ssl
import uuid
import base64
from datetime import date, datetime, timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_TV_IP,
    CONF_MEDIA_FOLDER,
    CONF_TOKEN_FILE,
    CONF_CALENDAR_ENTITY,
    CONF_LANGUAGE,
    CONF_UPCOMING_DAYS,
    CONF_MATTE_COLOR,
    CONF_OVERLAY_OPACITY,
    CONF_DEBUG_SAVE,
    CONF_FONT_SIZE,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_MATTE_COLOR,
    DEFAULT_LANGUAGE,
    DEFAULT_OVERLAY_OPACITY,
    DEFAULT_DEBUG_SAVE,
    DEFAULT_FONT_SIZE,
    SERVICE_UPDATE,
)
from .overlay import compose_overlay

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["button", "image", "number", "switch"]

SERVICE_UPDATE_SCHEMA = vol.Schema({
    vol.Optional("image_path"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Samsung Frame Art from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_update(call: ServiceCall) -> None:
        config = {**entry.data, **entry.options}

        tv_ip           = config[CONF_TV_IP]
        media_folder    = config[CONF_MEDIA_FOLDER]
        token_file      = config.get(CONF_TOKEN_FILE, "/config/samsung_frame_token.txt")
        calendar_entity = config.get(CONF_CALENDAR_ENTITY, "")
        lang            = config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        upcoming_days   = int(config.get(CONF_UPCOMING_DAYS, DEFAULT_UPCOMING_DAYS))
        matte           = config.get(CONF_MATTE_COLOR, DEFAULT_MATTE_COLOR)
        opacity         = int(config.get(CONF_OVERLAY_OPACITY, DEFAULT_OVERLAY_OPACITY))
        image_path      = call.data.get("image_path")

        # Read font_size and debug_save from HA entity states
        ent_reg = er.async_get(hass)

        def _state_by_unique_id(unique_id):
            entry_obj = ent_reg.async_get_entity_id_from_unique_id(unique_id) if hasattr(ent_reg, "async_get_entity_id_from_unique_id") else None
            if entry_obj is None:
                # fallback: scan registry
                for e in ent_reg.entities.values():
                    if e.unique_id == unique_id:
                        return hass.states.get(e.entity_id)
            else:
                return hass.states.get(entry_obj)
            return None

        fs_state = _state_by_unique_id(f"{entry.entry_id}_font_size")
        font_size = int(float(fs_state.state)) if fs_state and fs_state.state not in ("unknown", "unavailable") else DEFAULT_FONT_SIZE

        ds_state = _state_by_unique_id(f"{entry.entry_id}_debug_save")
        debug_save = (ds_state.state == "on") if ds_state and ds_state.state not in ("unknown", "unavailable") else False

        _LOGGER.info("font_size=%s debug_save=%s", font_size, debug_save)

        # ── Pick a random image ───────────────────────────────────────────────
        if not image_path:
            def _list_images(folder):
                if not os.path.isdir(folder):
                    return []
                return [
                    os.path.join(folder, f)
                    for f in os.listdir(folder)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                    and not f.startswith("frame_")  # skip debug saves
                ]
            images = await hass.async_add_executor_job(_list_images, media_folder)
            if not images:
                _LOGGER.error("No images found in %s", media_folder)
                return
            image_path = random.choice(images)
            _LOGGER.info("Selected image: %s", image_path)

        # ── Fetch calendar events ─────────────────────────────────────────────
        events = []
        if calendar_entity:
            try:
                now = dt_util.now()
                end = now + timedelta(days=upcoming_days)
                calendar_events = await hass.services.async_call(
                    "calendar", "get_events",
                    {
                        "entity_id": calendar_entity,
                        "start_date_time": now.isoformat(),
                        "end_date_time": end.isoformat(),
                    },
                    blocking=True,
                    return_response=True,
                )
                raw = (calendar_events or {}).get(calendar_entity, {}).get("events", [])
                for ev in raw:
                    start = ev.get("start")
                    end_dt = ev.get("end")
                    if isinstance(start, str):
                        try:
                            start = datetime.fromisoformat(start)
                        except ValueError:
                            try:
                                start = date.fromisoformat(start)
                            except ValueError:
                                continue
                    if isinstance(end_dt, str):
                        try:
                            end_dt = datetime.fromisoformat(end_dt)
                        except ValueError:
                            try:
                                end_dt = date.fromisoformat(end_dt)
                            except ValueError:
                                end_dt = None
                    if isinstance(start, datetime) and start.tzinfo is not None:
                        start = start.replace(tzinfo=None)
                    if isinstance(end_dt, datetime) and end_dt is not None and end_dt.tzinfo is not None:
                        end_dt = end_dt.replace(tzinfo=None)
                    all_day = isinstance(start, date) and not isinstance(start, datetime)
                    events.append({
                        "summary": ev.get("summary", ""),
                        "start": start,
                        "end": end_dt,
                        "all_day": all_day,
                    })
                events.sort(key=lambda e: (
                    e["start"] if isinstance(e["start"], datetime)
                    else datetime.combine(e["start"], datetime.min.time())
                ))
                _LOGGER.info("Fetched %d calendar events", len(events))
            except Exception as exc:
                _LOGGER.warning("Could not fetch calendar events: %s", exc)

        # ── Compose overlay ───────────────────────────────────────────────────
        try:
            jpeg_bytes = await hass.async_add_executor_job(
                compose_overlay, image_path, lang, events, opacity, font_size
            )
        except Exception as exc:
            _LOGGER.error("Failed to compose overlay: %s", exc)
            return

        # ── Update image entity ───────────────────────────────────────────────
        image_entity = hass.data[DOMAIN].get(f"{entry.entry_id}_image_entity")
        if image_entity:
            await hass.async_add_executor_job(image_entity.update_image, jpeg_bytes)

        # ── Debug save ────────────────────────────────────────────────────────
        if debug_save:
            ts = datetime.now().strftime("%d%m%Y%H%M%S")
            debug_path = os.path.join(media_folder, f"frame_{ts}.jpg")
            try:
                with open(debug_path, "wb") as f:
                    f.write(jpeg_bytes)
                _LOGGER.info("Debug image saved: %s", debug_path)
            except Exception as exc:
                _LOGGER.warning("Could not save debug image: %s", exc)

        # ── Push to TV ────────────────────────────────────────────────────────
        try:
            await hass.async_add_executor_job(
                _push_to_tv, tv_ip, token_file, jpeg_bytes, matte
            )
        except Exception as exc:
            _LOGGER.error("Failed to push image to TV: %s", exc)
            return

        _LOGGER.info("Successfully pushed art to Samsung Frame at %s", tv_ip)

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE, handle_update, schema=SERVICE_UPDATE_SCHEMA,
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


def _recv_until(conn, sub_events, max_msgs=15):
    for _ in range(max_msgs):
        try:
            raw = conn.recv()
        except Exception:
            break
        resp = json.loads(raw)
        if resp.get("event") == "d2d_service_message":
            data_str = resp.get("data", "{}")
            data = json.loads(data_str) if isinstance(data_str, str) else data_str
            if data.get("event") in sub_events:
                return data
    return None


def _push_to_tv(tv_ip, token_file, jpeg_bytes, matte):
    """Push image using WebSocket binary frame (Art API 0.97 — 2019 Frame)."""
    import websocket as ws_lib
    import time

    name_b64 = base64.b64encode(b"SamsungTvRemote").decode("utf-8")
    sslopt = {"cert_reqs": ssl.CERT_NONE}

    token = ""
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file) as f:
                token = f.readline().strip()
        except Exception:
            pass

    art_url = f"wss://{tv_ip}:8002/api/v2/channels/com.samsung.art-app?name={name_b64}"
    if token:
        art_url += f"&token={token}"

    conn = ws_lib.create_connection(art_url, timeout=10, sslopt=sslopt)
    conn.settimeout(8)

    try:
        for _ in range(10):
            raw = conn.recv()
            resp = json.loads(raw)
            event = resp.get("event", "")
            if event == "ms.channel.connect":
                new_token = resp.get("data", {}).get("token")
                if new_token and token_file:
                    with open(token_file, "w") as f:
                        f.write(new_token)
            elif event == "ms.channel.ready":
                break

        upload_id = str(uuid.uuid4())
        inner = {"request": "send_image", "file_type": "JPEG", "matte_id": matte or "none", "id": upload_id}
        outer = {"method": "ms.channel.emit", "params": {"data": json.dumps(inner), "to": "host", "event": "art_app_request"}}
        header = json.dumps(outer, separators=(",", ":")).encode("utf-8")
        payload = len(header).to_bytes(2, "big") + header + jpeg_bytes
        conn.send_binary(payload)

        data = _recv_until(conn, ["image_added", "error"])
        if data is None:
            _LOGGER.warning("No image_added confirmation")
            return
        if data.get("event") == "error":
            raise RuntimeError(f"TV error: {data}")

        content_id = data.get("content_id")
        _LOGGER.info("Image added, content_id=%s", content_id)

        if content_id:
            conn.send(json.dumps({
                "method": "ms.channel.emit",
                "params": {
                    "event": "art_app_request",
                    "to": "host",
                    "data": json.dumps({"request": "select_image", "content_id": content_id, "show": True}),
                },
            }))
            time.sleep(1)

    finally:
        conn.close()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE)
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
