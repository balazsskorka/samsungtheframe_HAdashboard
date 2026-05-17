"""Switch entity for Samsung Frame Art — debug save."""
from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SamsungFrameDebugSave(entry)])


class SamsungFrameDebugSave(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Debug Save"
    _attr_is_on = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_debug_save"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)},
                                  "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})"}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._attr_is_on = state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
