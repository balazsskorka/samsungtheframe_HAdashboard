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
    async_add_entities([SamsungFrameFontSize(entry), SamsungFrameOpacity(entry), SamsungFrameDaysToShow(entry), SamsungFrameBrightness(entry)])


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


class SamsungFrameOpacity(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Overlay Opacity"
    _attr_native_min_value = 10
    _attr_native_max_value = 90
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:opacity"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_opacity"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)},
                                  "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})"}
        self._attr_native_value = 5.0

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
    def opacity(self) -> int:
        return int(self._attr_native_value)


class SamsungFrameDaysToShow(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Calendar Days to Show"
    _attr_native_min_value = 1
    _attr_native_max_value = 14
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:calendar-range"
    _attr_native_unit_of_measurement = "days"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_days_to_show"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }
        self._attr_native_value = 1.0

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state not in ("unknown", "unavailable"):
            try:
                self._attr_native_value = float(int(float(state.state)))
            except ValueError:
                pass

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = float(int(value))
        self.async_write_ha_state()


class SamsungFrameBrightness(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Art Mode Brightness"
    _attr_native_min_value = 1
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = ""
    _attr_icon = "mdi:brightness-6"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_brightness"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }
        self._attr_native_value = 50.0

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
