"""Select entity for Samsung Frame Art — language picker."""
from __future__ import annotations
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, DEFAULT_LANGUAGE, LANGUAGES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SamsungFrameLanguageSelect(entry), SamsungFrameWeatherSelect(entry)])


class SamsungFrameLanguageSelect(SelectEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Language"
    _attr_icon = "mdi:translate"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_language"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }
        self._attr_options = list(LANGUAGES.values())  # ["English", "Deutsch", "Magyar"]
        self._attr_current_option = LANGUAGES.get(DEFAULT_LANGUAGE, "English")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state in self._attr_options:
            self._attr_current_option = state.state

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()

    @property
    def language_code(self) -> str:
        """Return the language code (en/de/hu) for the selected option."""
        for code, label in LANGUAGES.items():
            if label == self._attr_current_option:
                return code
        return DEFAULT_LANGUAGE


class SamsungFrameWeatherSelect(SelectEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Weather Entity"
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_weather_entity"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Samsung Frame ({entry.data.get('tv_ip', '')})",
        }
        self._attr_options = ["none"]
        self._attr_current_option = "none"
        self._weather_entities: list[str] = []

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Populate options from available weather entities
        weather_states = [
            s.entity_id for s in self.hass.states.async_all("weather")
        ]
        self._attr_options = ["none"] + weather_states
        # Restore previous selection
        state = await self.async_get_last_state()
        if state and state.state in self._attr_options:
            self._attr_current_option = state.state
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
