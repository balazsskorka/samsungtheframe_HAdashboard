"""Switch entities for Samsung Frame Art."""
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
    async_add_entities([
        SamsungFrameSwitch(entry, "debug_save",    "Debug Save",         "mdi:content-save",   False),
        SamsungFrameSwitch(entry, "show_date",     "Show Date Panel",    "mdi:calendar-today", True),
        SamsungFrameSwitch(entry, "show_calendar", "Show Calendar Panel","mdi:calendar-month", True),
        SamsungFrameSwitch(entry, "show_weather",  "Show Weather Forecast","mdi:weather-sunny",  True),
    ])


class SamsungFrameSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, key: str, name: str, icon: str, default: bool) -> None:
        self._entry = entry
        self._key = key
        self._default = default
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_is_on = default
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            self._attr_is_on = state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
