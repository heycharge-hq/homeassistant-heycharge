"""Config flow for HeyCharge Gateway integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
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

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None
        self._discovered_device_id: str | None = None

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

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle a flow initialized by zeroconf discovery.

        The firmware advertises ``_heycharge._tcp`` on port 80 with TXT
        records ``device_id``, ``model``, ``mode``, ``fwver``, ``build``,
        ``api_path`` and (optionally) ``name``. See
        ``src/modules/app/app_consumer_gateway.cpp::_registerMDNSDiscovery``.
        """
        properties = discovery_info.properties or {}
        device_id = properties.get("device_id")
        if not device_id:
            return self.async_abort(reason="no_device_id")

        host = f"http://{discovery_info.host}"

        await self.async_set_unique_id(device_id)
        # If already configured, update the host in case DHCP gave the
        # device a new IP since the last successful connection.
        self._abort_if_unique_id_configured(updates={"host": host})

        self._discovered_host = host
        self._discovered_device_id = device_id
        self._discovered_name = (
            properties.get("name")
            or properties.get("model")
            or "HeyCharge Gateway"
        )

        # Title placeholder shown on the discovery card in HA's UI.
        self.context["title_placeholders"] = {"name": self._discovered_name}

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm a zeroconf-discovered device with the user."""
        assert self._discovered_host is not None
        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass, {CONF_HOST: self._discovered_host}
                )
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")

            return self.async_create_entry(
                title=info["title"],
                data={"host": info["host"]},
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._discovered_name or ""},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
