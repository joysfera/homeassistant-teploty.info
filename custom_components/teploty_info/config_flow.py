"""Config flow for Teploty.info."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    TeplotyInfoApiClient,
    TeplotyInfoAuthError,
    TeplotyInfoConnectionError,
)
from .const import CONF_API_KEY, DOMAIN


class TeplotyInfoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Teploty.info setup flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for credentials and validate them against the API."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            api_key = user_input[CONF_API_KEY].strip()
            errors = await self._validate_credentials(username, api_key)
            if not errors:
                await self.async_set_unique_id(username.casefold())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Teploty.info ({username})",
                    data={CONF_USERNAME: username, CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_API_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, _entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Start reauthentication when the API key no longer works."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and save a replacement API key."""
        entry = self._reauth_entry
        errors: dict[str, str] = {}
        if user_input is not None:
            username = entry.data[CONF_USERNAME]
            api_key = user_input[CONF_API_KEY].strip()
            errors = await self._validate_credentials(username, api_key)
            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={CONF_USERNAME: username, CONF_API_KEY: api_key},
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    )
                }
            ),
            errors=errors,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
        )

    async def _validate_credentials(
        self, username: str, api_key: str
    ) -> dict[str, str]:
        """Return a config-flow error when credentials or the service fail."""
        client = TeplotyInfoApiClient(
            async_get_clientsession(self.hass), username, api_key
        )
        try:
            await client.async_get_data()
        except TeplotyInfoAuthError:
            return {"base": "invalid_auth"}
        except TeplotyInfoConnectionError:
            return {"base": "cannot_connect"}
        return {}
