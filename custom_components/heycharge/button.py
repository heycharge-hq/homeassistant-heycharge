"""Support for HeyCharge CONNECT buttons."""
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
    """Set up HeyCharge CONNECT button based on a config entry."""
    coordinator: HeyChargeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([HeyChargeEndSessionButton(coordinator, entry)])


class HeyChargeEndSessionButton(CoordinatorEntity, ButtonEntity):
    """Representation of a HeyCharge CONNECT end session button."""

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
            "model": coordinator.product or "GW-LITE",
            "sw_version": coordinator.sw_version,
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_end_session()
