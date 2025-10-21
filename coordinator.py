"""Data update coordinator for DINUSO BLE Thermometer using HA Bluetooth API."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    async_register_callback,
    BluetoothServiceInfoBleak,
)

from .const import (
    DOMAIN,
    TARGET_UUID,
    SCAN_INTERVAL,
    DEVICE_TIMEOUT,
    CONF_MAC_ADDRESS,
    RSSI_EXCELLENT,
    RSSI_GOOD,
    RSSI_FAIR,
)

_LOGGER = logging.getLogger(__name__)


class DinusoBleCoordinator(DataUpdateCoordinator):
    """Coordinator for DINUSO BLE Thermometer using Home Assistant Bluetooth API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self.target_mac = entry.data.get(CONF_MAC_ADDRESS)
        self._last_seen: datetime | None = None
        self._last_valid_data: dict[str, Any] = {}
        self._unregister_callback: Callable | None = None

    async def async_config_entry_first_refresh(self):
        """Set up Bluetooth callback."""
        @callback
        def handle_bluetooth_event(
            service_info: BluetoothServiceInfoBleak, change: BluetoothChange
        ):
            if self.target_mac and service_info.address.lower() != self.target_mac.lower():
                return

            payload = service_info.service_data.get(TARGET_UUID)
            if not payload:
                return

            decode_result = self._decode_temperature(payload)
            if decode_result is None:
                return

            temp_c, temp_int, raw_val, battery_bars, battery_percent = decode_result
            rssi = service_info.rssi
            connection_quality = self._get_connection_quality(rssi)

            self._last_seen = datetime.now(timezone.utc)
            self._last_valid_data = {
                "connected": True,
                "temperature": temp_c,
                "temperature_int": temp_int,
                "battery_level": battery_percent,
                "battery_bars": battery_bars,
                "rssi": rssi,
                "connection_quality": connection_quality,
                "last_seen": self._last_seen,
                "raw_value": raw_val,
                "mac_address": service_info.address,
            }
            self.async_set_updated_data(self._last_valid_data)

        # FIX: Pass service_uuids as a list instead of a set to avoid dictionary update error
        self._unregister_callback = async_register_callback(
            self.hass,
            handle_bluetooth_event,
            None,  # Match all service info
            BluetoothScanningMode.PASSIVE,
        )
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        is_connected = (
            self._last_seen is not None and (now - self._last_seen) <= DEVICE_TIMEOUT
        )

        if is_connected:
            return self._last_valid_data
        else:
            disconnected_data = self._last_valid_data.copy() if self._last_valid_data else {}
            disconnected_data.update({
                "connected": False,
                "connection_quality": "Disconnected",
            })
            return disconnected_data

    async def async_shutdown(self) -> None:
        if self._unregister_callback:
            self._unregister_callback()
            self._unregister_callback = None

    def _decode_temperature(self, raw_bytes: bytes) -> tuple[float, int, int, int, int] | None:
        if len(raw_bytes) < 6:
            return None
        try:
            raw_val = raw_bytes[4] | (raw_bytes[5] << 8)
            temp_c = (raw_val * 0.0625) - 50.0625
            temp_int = int(round(temp_c))
            battery_bars = 0
            battery_percent = 0
            
            # Battery is at position 7 in the service data payload
            # (position 11 in full advertisement - 4 bytes header offset)
            if len(raw_bytes) > 7:
                battery_byte = raw_bytes[7]  # Changed from 11 to 7
                battery_voltage = battery_byte * 0.03125
                
                _LOGGER.debug(
                    "Battery debug - byte[7]: %d (0x%02x), voltage: %.3fV",
                    battery_byte, battery_byte, battery_voltage
                )
                
                if battery_voltage >= 2.0:
                    battery_bars = 3
                elif battery_voltage >= 1.7:
                    battery_bars = 2
                elif battery_voltage >= 1.5:
                    battery_bars = 1
                else:
                    battery_bars = 0
                
                battery_percent = int((battery_bars / 3) * 100)
                
                _LOGGER.debug(
                    "Battery result - bars: %d, percent: %d",
                    battery_bars, battery_percent
                )
                
            return temp_c, temp_int, raw_val, battery_bars, battery_percent
        except Exception as err:
            _LOGGER.error("Failed to decode temperature data: %s", err)
            return None
        
    def _get_connection_quality(self, rssi: int) -> str:
        if rssi >= RSSI_EXCELLENT:
            return "Excellent"
        elif rssi >= RSSI_GOOD:
            return "Good"
        elif rssi >= RSSI_FAIR:
            return "Fair"
        else:
            return "Poor"
