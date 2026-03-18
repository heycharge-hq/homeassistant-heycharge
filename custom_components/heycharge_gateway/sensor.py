"""Support for HeyCharge Gateway sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeyChargeDataUpdateCoordinator


@dataclass
class HeyChargeSensorEntityDescription(SensorEntityDescription):
    """Describes HeyCharge sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None


SENSORS: tuple[HeyChargeSensorEntityDescription, ...] = (
    HeyChargeSensorEntityDescription(
        key="current_request",
        name="Current Request",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("current_request"),
    ),
    HeyChargeSensorEntityDescription(
        key="charging_current_l1",
        name="Charging Current L1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("charging_current_l1"),
    ),
    HeyChargeSensorEntityDescription(
        key="charging_current_l2",
        name="Charging Current L2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("charging_current_l2"),
    ),
    HeyChargeSensorEntityDescription(
        key="charging_current_l3",
        name="Charging Current L3",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("charging_current_l3"),
    ),
    HeyChargeSensorEntityDescription(
        key="charging_power",
        name="Charging Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("charging_power"),
    ),
    HeyChargeSensorEntityDescription(
        key="kwh_delivered",
        name="kWh Delivered",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["status"].get("kwh_delivered"),
    ),
    HeyChargeSensorEntityDescription(
        key="last_session_energy",
        name="Last Session Energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data["status"].get("last_session_energy"),
    ),
    HeyChargeSensorEntityDescription(
        key="last_session_duration",
        name="Last Session Duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("last_session_duration"),
    ),
    HeyChargeSensorEntityDescription(
        key="current_session_duration",
        name="Current Session Duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["status"].get("current_session_duration"),
    ),
    HeyChargeSensorEntityDescription(
        key="charger_state",
        name="Charger State",
        icon="mdi:state-machine",
        value_fn=lambda data: data["status"].get("charger_state"),
    ),
    HeyChargeSensorEntityDescription(
        key="p14a_current_limit",
        name="P14a Current Limit",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data["status"].get("p14a_current_limit"),
    ),
)

# Conditional sensor: only created when company car mode is enabled
SESSION_TYPE_SENSOR = HeyChargeSensorEntityDescription(
    key="session_type",
    name="Session Type",
    icon="mdi:account-badge",
    value_fn=lambda data: data["status"].get("session_type"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HeyCharge Gateway sensor based on a config entry."""
    coordinator: HeyChargeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HeyChargeSensor(coordinator, description, entry)
        for description in SENSORS
    ]

    # Conditionally add session_type sensor when company car mode is enabled
    config = coordinator.data.get("config", {})
    if config.get("company_car_mode", False):
        entities.append(HeyChargeSensor(coordinator, SESSION_TYPE_SENSOR, entry))

    async_add_entities(entities)


class HeyChargeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HeyCharge Gateway sensor."""

    entity_description: HeyChargeSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeyChargeDataUpdateCoordinator,
        description: HeyChargeSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None
