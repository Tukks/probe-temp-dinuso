"""Data update coordinator for DINUSO BLE Thermometer."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
    """Class to manage fetching data from DINUSO BLE device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self.target_mac = entry.data.get(CONF_MAC_ADDRESS)
        self._scanner: BleakScanner | None = None
        self._last_seen: datetime | None = None
        self._scanning = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from BLE device."""
        if not self._scanning:
            await self._start_scanning()

        # Check if device is still connected (received data recently)
        now = datetime.now(timezone.utc)
        if self._last_seen and (now - self._last_seen) > DEVICE_TIMEOUT:
            return {
                "connected": False,
                "temperature": None,
                "temperature_int": None,
                "battery_level": None,
                "battery_bars": None,
                "rssi": None,
                "connection_quality": "Disconnected",
                "last_seen": self._last_seen,
            }

        return self.data or {}

    async def _start_scanning(self) -> None:
        """Start BLE scanning."""
        if self._scanning:
            return

        try:
            self._scanner = BleakScanner(detection_callback=self._detection_callback)
            await self._scanner.start()
            self._scanning = True
            _LOGGER.debug("Started BLE scanning for DINUSO devices")
        except Exception as err:
            _LOGGER.error("Failed to start BLE scanning: %s", err)
            raise UpdateFailed(f"Failed to start BLE scanning: {err}") from err

    async def async_shutdown(self) -> None:
        """Stop scanning and cleanup."""
        if self._scanner and self._scanning:
            try:
                await self._scanner.stop()
                _LOGGER.debug("Stopped BLE scanning")
            except Exception as err:
                _LOGGER.error("Error stopping BLE scanner: %s", err)
            finally:
                self._scanning = False
                self._scanner = None

    def _detection_callback(
        self, device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Handle BLE advertisement detection."""
        # Check if this device matches our target (if specific MAC is configured)
        if self.target_mac and device.address.lower() != self.target_mac.lower():
            return

        # Check for target UUID in service data
        if TARGET_UUID not in (advertisement_data.service_data or {}):
            return

        payload = advertisement_data.service_data[TARGET_UUID]
        if not isinstance(payload, bytes):
            if isinstance(payload, str):
                try:
                    payload = bytes.fromhex(payload)
                except ValueError:
                    return
            else:
                return

        # Decode temperature and battery data
        decode_result = self._decode_temperature(payload)
        if decode_result is None:
            return

        temp_c, temp_int, raw_val, battery_bars, battery_percent = decode_result
        
        # Calculate connection quality from RSSI
        rssi = advertisement_data.rssi
        connection_quality = self._get_connection_quality(rssi)

        self._last_seen = datetime.now(timezone.utc)

        # Update coordinator data
        new_data = {
            "connected": True,
            "temperature": temp_c,
            "temperature_int": temp_int,
            "battery_level": battery_percent,
            "battery_bars": battery_bars,
            "rssi": rssi,
            "connection_quality": connection_quality,
            "last_seen": self._last_seen,
            "raw_value": raw_val,
            "mac_address": device.address,
        }

        # Trigger update to Home Assistant
        self.async_set_updated_data(new_data)

    def _decode_temperature(self, raw_bytes: bytes) -> tuple[float, int, int, int, int] | None:
        """Decode temperature from the 16-byte service data payload."""
        if len(raw_bytes) < 6:
            return None

        try:
            # Little-endian 16-bit from bytes[4] (LSB) and bytes[5] (MSB)
            raw_val = raw_bytes[4] | (raw_bytes[5] << 8)

            # Java formula: temp = (raw * 0.0625) - 50.0625
            temp_c = (raw_val * 0.0625) - 50.0625
            temp_int = int(round(temp_c))

            # Battery from byte[11]
            battery_bars = 0
            battery_percent = 0
            if len(raw_bytes) > 11:
                battery_byte = raw_bytes[11]
                battery_level = battery_byte * 0.03125

                # Convert to percentage (0-100%)
                battery_percent = max(0, min(100, int(battery_level * 50)))

                if battery_level >= 2.0:
                    battery_bars = 3
                elif battery_level >= 1.7:
                    battery_bars = 2
                elif battery_level >= 1.5:
                    battery_bars = 1
                else:
                    battery_bars = 0

            return temp_c, temp_int, raw_val, battery_bars, battery_percent

        except Exception as err:
            _LOGGER.error("Failed to decode temperature data: %s", err)
            return None

    def _get_connection_quality(self, rssi: int) -> str:
        """Get connection quality string from RSSI value."""
        if rssi >= RSSI_EXCELLENT:
            return "Excellent"
        elif rssi >= RSSI_GOOD:
            return "Good"
        elif rssi >= RSSI_FAIR:
            return "Fair"
        else:
            return "Poor"