"""Data update coordinator for Teploty.info."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    TeplotyInfoApiClient,
    TeplotyInfoAuthError,
    TeplotyInfoConnectionError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TeplotyInfoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch all account sensors in one request per update."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: TeplotyInfoApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest sensor inventory and values."""
        try:
            return await self.client.async_get_data()
        except TeplotyInfoAuthError as err:
            raise ConfigEntryAuthFailed from err
        except TeplotyInfoConnectionError as err:
            raise UpdateFailed(str(err)) from err
