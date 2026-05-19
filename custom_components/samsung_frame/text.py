"""Text entities for Samsung Frame Art — folder path and file name."""
from __future__ import annotations
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, DEFAULT_MEDIA_FOLDER


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([
        SamsungFrameMatteColorEntity(entry),
        SamsungFrameTextEntity(
            entry,
            key="folder_path",
            name="Image Folder",
            icon="mdi:folder-image",
            placeholder=DEFAULT_MEDIA_FOLDER,
            pattern=None,
        ),
        SamsungFrameTextEntity(
            entry,
            key="file_name",
            name="Image File Name",
            icon="mdi:file-image",
            placeholder="random",
            pattern=None,
        ),
    ])


class SamsungFrameTextEntity(TextEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_native_min = 0
    _attr_native_max = 255

    def __init__(
        self,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        placeholder: str,
        pattern: str | None,
    ) -> None:
        self._entry = entry
        self._key = key
        self._placeholder = placeholder
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_value = ""
        self._attr_pattern = pattern
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            self._attr_native_value = state.state

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value.strip()
        self.async_write_ha_state()


class SamsungFrameMatteColorEntity(TextEntity, RestoreEntity):
    """Text entity storing a hex color for the digital matte, rendered as color picker in UI."""
    _attr_has_entity_name = True
    _attr_name = "Digital Matte Color"
    _attr_icon = "mdi:palette"
    _attr_native_min = 4
    _attr_native_max = 7
    _attr_pattern = "^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$"
    _attr_native_value = "#F5F0E8"  # warm white default

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_matte_color"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            self._attr_native_value = state.state

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value.strip()
        self.async_write_ha_state()
