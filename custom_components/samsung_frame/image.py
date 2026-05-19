"""Image entity for Samsung Frame Art — last generated image."""
from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Optional

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entity = SamsungFrameLastImage(hass, entry)
    async_add_entities([entity])
    # Store reference so __init__.py can update it
    hass.data[DOMAIN][f"{entry.entry_id}_image_entity"] = entity


class SamsungFrameLastImage(ImageEntity):
    _attr_has_entity_name = True
    _attr_name = "Last Generated Image"
    _attr_icon = "mdi:image-frame"
    _attr_content_type = "image/jpeg"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_image"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }
        self._jpeg_bytes: Optional[bytes] = None
        self._attr_image_last_updated = None

    def update_image(self, jpeg_bytes: bytes) -> None:
        """Called from __init__.py after composing the overlay."""
        self._jpeg_bytes = jpeg_bytes
        self._attr_image_last_updated = datetime.now()
        self.schedule_update_ha_state()

    async def async_image(self) -> Optional[bytes]:
        return self._jpeg_bytes
