"""Config flow for Samsung Frame Art integration."""
from __future__ import annotations

import os
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DEFAULT_MEDIA_FOLDER,
    DEFAULT_TOKEN_FILE,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_MATTE_COLOR,
    DEFAULT_LANGUAGE,
    DEFAULT_OVERLAY_OPACITY,
    DEFAULT_DEBUG_SAVE,
    LANGUAGES,
    MATTE_OPTIONS,
)


class SamsungFrameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            media_folder = user_input[CONF_MEDIA_FOLDER]

            def _check():
                if not os.path.isdir(media_folder):
                    return "invalid_path"
                images = [f for f in os.listdir(media_folder)
                          if f.lower().endswith((".jpg", ".jpeg", ".png"))]
                if not images:
                    return "no_images"
                return None

            import asyncio
            err = await asyncio.get_event_loop().run_in_executor(None, _check)
            if err:
                errors[CONF_MEDIA_FOLDER] = err
            else:
                await self.async_set_unique_id(user_input[CONF_TV_IP])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Samsung Frame ({user_input[CONF_TV_IP]})",
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required(CONF_TV_IP): str,
            vol.Required(CONF_MEDIA_FOLDER, default=DEFAULT_MEDIA_FOLDER): str,
            vol.Required(CONF_TOKEN_FILE, default=DEFAULT_TOKEN_FILE): str,
            vol.Optional(CONF_CALENDAR_ENTITY, default=""): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar")
            ),
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": k, "label": v} for k, v in LANGUAGES.items()],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_UPCOMING_DAYS, default=DEFAULT_UPCOMING_DAYS): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=14, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_MATTE_COLOR, default=DEFAULT_MATTE_COLOR): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MATTE_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_OVERLAY_OPACITY, default=DEFAULT_OVERLAY_OPACITY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=90, step=5, mode=selector.NumberSelectorMode.SLIDER)
            ),
            vol.Optional(CONF_DEBUG_SAVE, default=DEFAULT_DEBUG_SAVE): selector.BooleanSelector(),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SamsungFrameOptionsFlow(config_entry)


class SamsungFrameOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema({
            vol.Required(CONF_TV_IP, default=current.get(CONF_TV_IP, "")): str,
            vol.Required(CONF_MEDIA_FOLDER, default=current.get(CONF_MEDIA_FOLDER, DEFAULT_MEDIA_FOLDER)): str,
            vol.Optional(CONF_CALENDAR_ENTITY, default=current.get(CONF_CALENDAR_ENTITY, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar")
            ),
            vol.Required(CONF_LANGUAGE, default=current.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": k, "label": v} for k, v in LANGUAGES.items()],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_UPCOMING_DAYS, default=current.get(CONF_UPCOMING_DAYS, DEFAULT_UPCOMING_DAYS)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=14, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_MATTE_COLOR, default=current.get(CONF_MATTE_COLOR, DEFAULT_MATTE_COLOR)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MATTE_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_OVERLAY_OPACITY, default=current.get(CONF_OVERLAY_OPACITY, DEFAULT_OVERLAY_OPACITY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=90, step=5, mode=selector.NumberSelectorMode.SLIDER)
            ),
            vol.Optional(CONF_DEBUG_SAVE, default=current.get(CONF_DEBUG_SAVE, DEFAULT_DEBUG_SAVE)): selector.BooleanSelector(),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
