"""Schermata di collegamento: indirizzo di NuvHome e chiave creata dal Profilo."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_API_KEY, CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN
from .coordinator import NuvHomeAuthError, fetch_summary


class NuvHomeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, base_url: str, api_key: str) -> str | None:
        try:
            await fetch_summary(self.hass, base_url, api_key)
        except NuvHomeAuthError:
            return "invalid_auth"
        except (ClientError, TimeoutError):
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip().rstrip("/")
            api_key = user_input[CONF_API_KEY].strip()
            error = await self._validate(base_url, api_key)
            if error:
                errors["base"] = error
            else:
                # Una chiave sola per collegamento: l'identificativo e' un'impronta, mai la chiave.
                await self.async_set_unique_id(hashlib.sha256(api_key.encode()).hexdigest()[:16])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="NuvHome", data={CONF_BASE_URL: base_url, CONF_API_KEY: api_key})
        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Required(CONF_API_KEY): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """La chiave e' stata revocata: se ne incolla una nuova."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            error = await self._validate(entry.data[CONF_BASE_URL], api_key)
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_API_KEY: api_key})
        return self.async_show_form(step_id="reauth_confirm", data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}), errors=errors)
