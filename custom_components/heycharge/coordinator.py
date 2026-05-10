"""DataUpdateCoordinator for HeyCharge CONNECT."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_CONFIG,
    API_CURRENT_LIMIT,
    API_END_SESSION,
    API_PAUSE,
    API_START_SESSION,
    API_STATUS,
    DEFAULT_LOCAL_API_PASSWORD,
    DEFAULT_SCAN_INTERVAL,
    LOCAL_API_USERNAME,
)

_LOGGER = logging.getLogger(__name__)


class HeyChargeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HeyCharge CONNECT data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        password: str = DEFAULT_LOCAL_API_PASSWORD,
    ) -> None:
        """Initialize."""
        self.host = host
        self.session = session
        self.config_data: dict[str, Any] = {}
        # Older firmware ignores Authorization headers and returns 200
        # regardless; new firmware enforces this. Either way we always
        # send the header — it's a no-op on devices that don't care.
        self._auth = aiohttp.BasicAuth(LOCAL_API_USERNAME, password)

        super().__init__(
            hass,
            _LOGGER,
            name="HeyCharge CONNECT",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def sw_version(self) -> str | None:
        """Build a sw_version string for device_info from cached config data.

        Returns "<fw_version> (<build_string>)" when both are present,
        falls back to whichever is available, or None if neither is.
        """
        fw = (self.config_data or {}).get("fw_version")
        build = (self.config_data or {}).get("build_string")
        if fw and build:
            return f"{fw} ({build})"
        return fw or build or None

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Fetch status data
            async with self.session.get(
                f"{self.host}{API_STATUS}",
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed(
                        "HeyCharge CONNECT rejected the admin password — re-enter it"
                    )
                if response.status != 200:
                    raise UpdateFailed(f"Error communicating with API: {response.status}")

                status_data = await response.json()

            # Fetch config data (less frequently - only if not cached)
            if not self.config_data:
                try:
                    async with self.session.get(
                        f"{self.host}{API_CONFIG}",
                        auth=self._auth,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        if response.status == 401:
                            raise ConfigEntryAuthFailed(
                                "HeyCharge CONNECT rejected the admin password — re-enter it"
                            )
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

    async def _post(self, path: str, payload: dict[str, Any], action: str) -> None:
        """Issue an authenticated POST and translate failures uniformly."""
        try:
            async with self.session.post(
                f"{self.host}{path}",
                json=payload,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed(
                        "HeyCharge CONNECT rejected the admin password — re-enter it"
                    )
                if response.status != 200:
                    raise UpdateFailed(f"Error {action}: {response.status}")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error {action}: {err}")

        # Request immediate refresh after a successful command
        await self.async_request_refresh()

    async def async_set_pause(self, paused: bool) -> None:
        """Set pause charging state."""
        await self._post(API_PAUSE, {"paused": paused}, "setting pause state")

    async def async_set_current_limit(self, limit: float) -> None:
        """Set current limit."""
        await self._post(API_CURRENT_LIMIT, {"limit": limit}, "setting current limit")

    async def async_start_session(self, session_type: str = "personal") -> None:
        """Start a charging session."""
        await self._post(API_START_SESSION, {"type": session_type}, "starting session")

    async def async_end_session(self) -> None:
        """End the current charging session."""
        await self._post(API_END_SESSION, {}, "ending session")
