"""DataUpdateCoordinator for HeyCharge Gateway."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_STATUS, API_CONFIG, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class HeyChargeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HeyCharge Gateway data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
    ) -> None:
        """Initialize."""
        self.host = host
        self.session = session
        self.config_data: dict[str, Any] = {}

        super().__init__(
            hass,
            _LOGGER,
            name="HeyCharge Gateway",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Fetch status data
            async with self.session.get(
                f"{self.host}{API_STATUS}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error communicating with API: {response.status}")

                status_data = await response.json()

            # Fetch config data (less frequently - only if not cached)
            if not self.config_data:
                try:
                    async with self.session.get(
                        f"{self.host}{API_CONFIG}",
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        if response.status == 200:
                            self.config_data = await response.json()
                except aiohttp.ClientError:
                    _LOGGER.warning("Failed to fetch config data, using cached data")

            # Combine status and config data
            return {
                "status": status_data,
                "config": self.config_data,
            }

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_set_pause(self, paused: bool) -> None:
        """Set pause charging state."""
        from .const import API_PAUSE

        try:
            async with self.session.post(
                f"{self.host}{API_PAUSE}",
                json={"paused": paused},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error setting pause state: {response.status}")

            # Request immediate refresh
            await self.async_request_refresh()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error setting pause state: {err}")

    async def async_set_current_limit(self, limit: float) -> None:
        """Set current limit."""
        from .const import API_CURRENT_LIMIT

        try:
            async with self.session.post(
                f"{self.host}{API_CURRENT_LIMIT}",
                json={"limit": limit},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error setting current limit: {response.status}")

            # Request immediate refresh
            await self.async_request_refresh()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error setting current limit: {err}")

    async def async_start_session(self, session_type: str = "personal") -> None:
        """Start a charging session."""
        from .const import API_START_SESSION

        try:
            async with self.session.post(
                f"{self.host}{API_START_SESSION}",
                json={"type": session_type},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error starting session: {response.status}")

            # Request immediate refresh
            await self.async_request_refresh()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error starting session: {err}")

    async def async_end_session(self) -> None:
        """End the current charging session."""
        from .const import API_END_SESSION

        try:
            async with self.session.post(
                f"{self.host}{API_END_SESSION}",
                json={},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error ending session: {response.status}")

            # Request immediate refresh
            await self.async_request_refresh()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error ending session: {err}")
