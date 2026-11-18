"""Legge il riassunto di NuvHome ogni mezz'ora (sola lettura)."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientTimeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_BASE_URL, DOMAIN, REQUEST_TIMEOUT, SUMMARY_PATH, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NuvHomeAuthError(Exception):
    """La chiave non e' valida o e' stata revocata."""


async def fetch_summary(hass: HomeAssistant, base_url: str, api_key: str) -> dict[str, Any]:
    """Chiede il riassunto a NuvHome. Alza NuvHomeAuthError se la chiave non vale."""
    session = async_get_clientsession(hass)
    url = f"{base_url.rstrip('/')}{SUMMARY_PATH}"
    async with session.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=ClientTimeout(total=REQUEST_TIMEOUT)) as response:
        if response.status == 401:
            raise NuvHomeAuthError
        response.raise_for_status()
        return await response.json()


class NuvHomeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Tiene in memoria l'ultimo riassunto: le case sono indicizzate per id."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            summary = await fetch_summary(self.hass, self.entry.data[CONF_BASE_URL], self.entry.data[CONF_API_KEY])
        except NuvHomeAuthError as error:
            raise ConfigEntryAuthFailed("Chiave NuvHome non valida o revocata") from error
        except (ClientError, TimeoutError) as error:
            raise UpdateFailed(f"NuvHome non risponde: {error}") from error
        return {house["id"]: house for house in summary.get("houses", [])}
