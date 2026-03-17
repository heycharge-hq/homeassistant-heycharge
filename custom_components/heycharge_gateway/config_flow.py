"""Config flow for HeyCharge Gateway integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, API_CONFIG

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]

    # Ensure host starts with http:// or https://
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"

    session = async_get_clientsession(hass)

    try:
        async with session.get(f"{host}{API_CONFIG}", timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise CannotConnect

            config_data = await response.json()

            # Return info that you want to store in the config entry.
            return {
                "title": config_data.get("charger_name", config_data.get("device_id", "HeyCharge Gateway")),
                "host": host,
                "device_id": config_data.get("device_id"),
            }
    except aiohttp.ClientError:
        raise CannotConnect
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception")
        raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HeyCharge Gateway."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID to prevent duplicate entries
                await self.async_set_unique_id(info["device_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data={"host": info["host"]})

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
