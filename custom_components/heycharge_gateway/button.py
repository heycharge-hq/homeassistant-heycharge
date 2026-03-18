"""Support for HeyCharge Gateway buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeyChargeDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HeyCharge Gateway button based on a config entry."""
    coordinator: HeyChargeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    buttons = [
        HeyChargeEndSessionButton(coordinator, entry),
    ]

    # Check if company car mode is enabled
    config = coordinator.data.get("config", {})
    if config.get("company_car_mode", False):
        buttons.append(HeyChargeStartPersonalSessionButton(coordinator, entry))
        buttons.append(HeyChargeStartCompanySessionButton(coordinator, entry))
    else:
        buttons.append(HeyChargeStartSessionButton(coordinator, entry))

    async_add_entities(buttons)


class HeyChargeStartSessionButton(CoordinatorEntity, ButtonEntity):
    """Representation of a HeyCharge Gateway start session button."""

    _attr_has_entity_name = True
    _attr_name = "Start Session Personal"
    _attr_icon = "mdi:play-circle"

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_start_session_personal"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_start_session("personal")


class HeyChargeStartPersonalSessionButton(CoordinatorEntity, ButtonEntity):
    """Representation of a HeyCharge Gateway start personal session button."""

    _attr_has_entity_name = True
    _attr_name = "Start Session (Personal)"
    _attr_icon = "mdi:play-circle"

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_start_session_personal"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_start_session("personal")


class HeyChargeStartCompanySessionButton(CoordinatorEntity, ButtonEntity):
    """Representation of a HeyCharge Gateway start company session button."""

    _attr_has_entity_name = True
    _attr_name = "Start Session (Company)"
    _attr_icon = "mdi:play-circle-outline"

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_start_session_company"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_start_session("company")


class HeyChargeEndSessionButton(CoordinatorEntity, ButtonEntity):
    """Representation of a HeyCharge Gateway end session button."""

    _attr_has_entity_name = True
    _attr_name = "End Session"
    _attr_icon = "mdi:stop-circle"

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_end_session"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_end_session()
