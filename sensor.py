"""Sensor platform for DINUSO BLE Thermometer."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    CONF_DEVICE_NAME,
    CONF_MAC_ADDRESS,
    SENSOR_TEMPERATURE,
    SENSOR_TEMPERATURE_INT,
    SENSOR_BATTERY_LEVEL,
    SENSOR_BATTERY_BARS,
    SENSOR_RSSI,
    SENSOR_CONNECTION_QUALITY,
)
from .coordinator import DinusoBleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: DinusoBleCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        DinusoTemperatureSensor(coordinator, config_entry, SENSOR_TEMPERATURE),
        DinusoTemperatureSensor(coordinator, config_entry, SENSOR_TEMPERATURE_INT),
        DinusoBatterySensor(coordinator, config_entry, SENSOR_BATTERY_LEVEL),
        DinusoBatteryBarsSensor(coordinator, config_entry, SENSOR_BATTERY_BARS),
        DinusoRssiSensor(coordinator, config_entry, SENSOR_RSSI),
        DinusoConnectionQualitySensor(coordinator, config_entry, SENSOR_CONNECTION_QUALITY),
    ]

    async_add_entities(entities)


class DinusoBaseSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Base class for DINUSO BLE sensors."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.sensor_type = sensor_type
        self._attr_has_entity_name = True
        
        device_name = config_entry.data[CONF_DEVICE_NAME]
        mac_address = config_entry.data.get(CONF_MAC_ADDRESS, "unknown")
        
        self._attr_unique_id = f"{mac_address}_{sensor_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Entities remain available even when disconnected, they just show last known values
        return self.coordinator.last_update_success and bool(self.coordinator.data)
    
    async def async_added_to_hass(self):
        """Restore last value if coordinator has no data yet."""
        await super().async_added_to_hass()
        if not self.coordinator.data:
            last_state = await self.async_get_last_state()
            if last_state is not None:
                self._attr_native_value = last_state.state


class DinusoTemperatureSensor(DinusoBaseSensor):
    """Temperature sensor for DINUSO BLE device."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, config_entry, sensor_type)
        
        if sensor_type == SENSOR_TEMPERATURE:
            self._attr_name = "Temperature"
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_suggested_display_precision = 1
        else:  # SENSOR_TEMPERATURE_INT
            self._attr_name = "Temperature (Integer)"
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | int | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None
            
        if self.sensor_type == SENSOR_TEMPERATURE:
            return self.coordinator.data.get("temperature")
        else:  # SENSOR_TEMPERATURE_INT
            return self.coordinator.data.get("temperature_int")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
            
        attrs = {}
        if last_seen := self.coordinator.data.get("last_seen"):
            if isinstance(last_seen, datetime):
                attrs["last_updated"] = last_seen.isoformat()
        
        if raw_value := self.coordinator.data.get("raw_value"):
            attrs["raw_value"] = raw_value

        # Add connection status to temperature sensors
        attrs["connected"] = self.coordinator.data.get("connected", False)
            
        return attrs


class DinusoBatterySensor(DinusoBaseSensor):
    """Battery level sensor for DINUSO BLE device."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, config_entry, sensor_type)
        self._attr_name = "Battery Level"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("battery_level")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
            
        attrs = {}
        if battery_bars := self.coordinator.data.get("battery_bars"):
            attrs["battery_bars"] = battery_bars

        attrs["connected"] = self.coordinator.data.get("connected", False)
            
        return attrs


class DinusoBatteryBarsSensor(DinusoBaseSensor):
    """Battery bars sensor for DINUSO BLE device."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the battery bars sensor."""
        super().__init__(coordinator, config_entry, sensor_type)
        self._attr_name = "Battery Bars"
        self._attr_icon = "mdi:battery"

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("battery_bars")

    @property
    def icon(self) -> str:
        """Return the icon based on battery level."""
        if not self.coordinator.data:
            return "mdi:battery-unknown"
            
        bars = self.coordinator.data.get("battery_bars", 0)
        icons = {
            0: "mdi:battery-outline",
            1: "mdi:battery-30",
            2: "mdi:battery-60", 
            3: "mdi:battery",
        }
        return icons.get(bars, "mdi:battery-unknown")


class DinusoRssiSensor(DinusoBaseSensor):
    """RSSI sensor for DINUSO BLE device."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the RSSI sensor."""
        super().__init__(coordinator, config_entry, sensor_type)
        self._attr_name = "Signal Strength"
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None
        # Only show RSSI when connected
        if not self.coordinator.data.get("connected", False):
            return None
        return self.coordinator.data.get("rssi")


class DinusoConnectionQualitySensor(DinusoBaseSensor):
    """Connection quality sensor for DINUSO BLE device."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the connection quality sensor."""
        super().__init__(coordinator, config_entry, sensor_type)
        self._attr_name = "Connection Quality"
        self._attr_icon = "mdi:signal"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("connection_quality")

    @property
    def icon(self) -> str:
        """Return the icon based on connection quality."""
        if not self.coordinator.data:
            return "mdi:signal-off"
            
        quality = self.coordinator.data.get("connection_quality", "").lower()
        icons = {
            "excellent": "mdi:signal-cellular-3",
            "good": "mdi:signal-cellular-2", 
            "fair": "mdi:signal-cellular-1",
            "poor": "mdi:signal-cellular-outline",
            "disconnected": "mdi:signal-off",
        }
        return icons.get(quality, "mdi:signal")