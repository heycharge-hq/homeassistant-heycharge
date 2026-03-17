"""Support for HeyCharge Gateway binary sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeyChargeDataUpdateCoordinator


@dataclass
class HeyChargeBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes HeyCharge binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool] | None = None


BINARY_SENSORS: tuple[HeyChargeBinarySensorEntityDescription, ...] = (
    HeyChargeBinarySensorEntityDescription(
        key="session_active",
        name="Charging",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data["status"].get("session_active", False),
    ),
    HeyChargeBinarySensorEntityDescription(
        key="heycharge_backend_enabled",
        name="HeyCharge Backend Enabled",
        icon="mdi:cloud-check",
        value_fn=lambda data: data["status"].get("heycharge_backend_enabled", False),
    ),
    HeyChargeBinarySensorEntityDescription(
        key="heycharge_backend_connected",
        name="HeyCharge Backend Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data["status"].get("heycharge_backend_connected", False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HeyCharge Gateway binary sensor based on a config entry."""
    coordinator: HeyChargeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        HeyChargeBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSORS
    )


class HeyChargeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a HeyCharge Gateway binary sensor."""

    entity_description: HeyChargeBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        description: HeyChargeBinarySensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "HeyCharge",
            "model": "GW-LITE",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False
