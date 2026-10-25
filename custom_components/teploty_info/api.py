"""HTTP client for the Teploty.info sensor endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import API_URL


class TeplotyInfoApiError(Exception):
    """Base error for the Teploty.info API."""


class TeplotyInfoAuthError(TeplotyInfoApiError):
    """The Teploty.info credentials were rejected."""


class TeplotyInfoConnectionError(TeplotyInfoApiError):
    """The API could not be reached or returned invalid data."""


class TeplotyInfoApiClient:
    """Small async client using the account API key in request headers."""

    def __init__(self, session: ClientSession, username: str, api_key: str) -> None:
        self._session = session
        self._headers = {
            "X-Teploty-Login": username,
            "X-Teploty-Key": api_key,
            "Accept": "application/json",
        }

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch all probe and sensor readings."""
        try:
            async with self._session.get(
                API_URL,
                headers=self._headers,
                timeout=ClientTimeout(total=20),
            ) as response:
                if response.status == 401:
                    raise TeplotyInfoAuthError("Invalid Teploty.info credentials")
                if response.status != 200:
                    raise TeplotyInfoConnectionError(
                        f"Teploty.info returned HTTP {response.status}"
                    )
                payload = await response.json()
        except TeplotyInfoApiError:
            raise
        except (ClientError, asyncio.TimeoutError, ValueError) as err:
            raise TeplotyInfoConnectionError(str(err)) from err

        if not isinstance(payload, dict) or not isinstance(payload.get("probes"), list):
            raise TeplotyInfoConnectionError("Unexpected response from Teploty.info")
        return payload
