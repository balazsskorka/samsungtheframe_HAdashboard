"""Number entity for Samsung Frame Art — font size."""
from __future__ import annotations
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, DEFAULT_FONT_SIZE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SamsungFrameFontSize(entry)])


class SamsungFrameFontSize(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Font Size"
    _attr_native_min_value = 50
    _attr_native_max_value = 200
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_font_size"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)},
                                  "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})"}
        self._attr_native_value = float(DEFAULT_FONT_SIZE)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            try:
                self._attr_native_value = float(state.state)
            except ValueError:
                pass

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def font_size(self) -> int:
        return int(self._attr_native_value)
