"""Button entity for Samsung Frame Art — trigger refresh."""
from __future__ import annotations
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SERVICE_UPDATE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SamsungFrameRefreshButton(entry), SamsungFrameDeleteAllButton(entry)])


class SamsungFrameRefreshButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Refresh Art"
    _attr_icon = "mdi:image-refresh"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }

    async def async_press(self) -> None:
        await self.hass.services.async_call(DOMAIN, SERVICE_UPDATE, {})


class SamsungFrameDeleteAllButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Delete All TV Images"
    _attr_icon = "mdi:delete-sweep"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_delete_all"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }

    async def async_press(self) -> None:
        await self.hass.services.async_call(DOMAIN, "delete_all_tv_images", {})
