"""Support for HeyCharge Gateway number entities."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
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
    """Set up HeyCharge Gateway number based on a config entry."""
    coordinator: HeyChargeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([HeyChargeCurrentLimitNumber(coordinator, entry)])


class HeyChargeCurrentLimitNumber(CoordinatorEntity, NumberEntity):
    """Representation of a HeyCharge Gateway current limit number."""

    _attr_has_entity_name = True
    _attr_name = "Current Limit"
    _attr_icon = "mdi:current-ac"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_current_limit"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

        # Get min/max from config
        config = coordinator.data.get("config", {})
        self._attr_native_min_value = config.get("min_current", 6)
        self._attr_native_max_value = config.get("max_current", 32)
        self._attr_native_step = 1

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.coordinator.data["status"].get("current_limit", 6)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.async_set_current_limit(value)
