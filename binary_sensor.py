"""Binary sensor platform for DINUSO BLE Thermometer."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    BINARY_SENSOR_CONNECTED,
)
from .coordinator import DinusoBleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: DinusoBleCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        DinusoConnectedBinarySensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class DinusoConnectedBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Connected binary sensor for DINUSO BLE device."""

    def __init__(
        self,
        coordinator: DinusoBleCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_has_entity_name = True
        self._attr_name = "Connected"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        
        device_name = config_entry.data[CONF_DEVICE_NAME]
        mac_address = config_entry.data.get(CONF_MAC_ADDRESS, "unknown")
        
        self._attr_unique_id = f"{mac_address}_{BINARY_SENSOR_CONNECTED}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0.0",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("connected", False)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
            
        attrs = {}
        if last_seen := self.coordinator.data.get("last_seen"):
            attrs["last_seen"] = last_seen.isoformat() if hasattr(last_seen, 'isoformat') else str(last_seen)
        
        if mac := self.coordinator.data.get("mac_address"):
            attrs["mac_address"] = mac
            
        return attrs