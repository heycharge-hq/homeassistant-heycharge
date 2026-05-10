"""Config flow for HeyCharge CONNECT integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    API_CONFIG,
    DEFAULT_LOCAL_API_PASSWORD,
    DOMAIN,
    LOCAL_API_USERNAME,
)

_LOGGER = logging.getLogger(__name__)

# Password is masked in the UI but pre-filled with the firmware default,
# so users on default-password devices (and on legacy no-auth firmware)
# can hit Submit without thinking about credentials.
_PASSWORD_FIELD = vol.Required(
    CONF_PASSWORD, default=DEFAULT_LOCAL_API_PASSWORD
)
_PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        _PASSWORD_FIELD: _PASSWORD_SELECTOR,
    }
)

STEP_ZEROCONF_CONFIRM_SCHEMA = vol.Schema(
    {
        _PASSWORD_FIELD: _PASSWORD_SELECTOR,
    }
)

STEP_REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): _PASSWORD_SELECTOR,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Probe the device's /config endpoint with the supplied password.

    Raises CannotConnect for network failures / non-401 errors and
    InvalidAuth specifically for HTTP 401, so the caller can render
    the right error message.
    """
    host = data[CONF_HOST]
    password = data.get(CONF_PASSWORD, DEFAULT_LOCAL_API_PASSWORD)

    # Ensure host starts with http:// or https://
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"

    session = async_get_clientsession(hass)
    auth = aiohttp.BasicAuth(LOCAL_API_USERNAME, password)

    try:
        async with session.get(
            f"{host}{API_CONFIG}",
            auth=auth,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == 401:
                raise InvalidAuth
            if response.status != 200:
                raise CannotConnect

            config_data = await response.json()

            return {
                "title": config_data.get(
                    "charger_name",
                    config_data.get("device_id", "HeyCharge CONNECT"),
                ),
                "host": host,
                "device_id": config_data.get("device_id"),
            }
    except aiohttp.ClientError:
        raise CannotConnect
    except (CannotConnect, InvalidAuth):
        raise
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception")
        raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HeyCharge CONNECT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None
        self._discovered_device_id: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

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
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID to prevent duplicate entries
                await self.async_set_unique_id(info["device_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: info["host"],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

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
            or "HeyCharge CONNECT"
        )

        # Title placeholder shown on the discovery card in HA's UI.
        self.context["title_placeholders"] = {"name": self._discovered_name}

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm a zeroconf-discovered device with the user."""
        assert self._discovered_host is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass,
                    {
                        CONF_HOST: self._discovered_host,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: info["host"],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=STEP_ZEROCONF_CONFIRM_SCHEMA,
            description_placeholders={"name": self._discovered_name or ""},
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle reauth — coordinator hit a 401 on a previously working entry."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Prompt the user for a fresh password."""
        assert self._reauth_entry is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(
                    self.hass,
                    {
                        CONF_HOST: self._reauth_entry.data[CONF_HOST],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate the device rejected the supplied password."""
