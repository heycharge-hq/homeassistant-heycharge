"""Support for HeyCharge Gateway switches."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up HeyCharge Gateway switch based on a config entry."""
    coordinator: HeyChargeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([HeyChargePauseSwitch(coordinator, entry)])


class HeyChargePauseSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a HeyCharge Gateway pause charging switch."""

    _attr_has_entity_name = True
    _attr_name = "Pause Charging"
    _attr_icon = "mdi:pause-circle"

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pause_charging"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on (charging is paused)."""
        return self.coordinator.data["status"].get("pause_charging", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch (pause charging)."""
        await self.coordinator.async_set_pause(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch (resume charging)."""
        await self.coordinator.async_set_pause(False)
