"""Constants for the DINUSO BLE Thermometer integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "dinuso_ble"
MANUFACTURER: Final = "DINUSO"
MODEL: Final = "BLE Meat Thermometer"

# BLE Configuration
TARGET_UUID: Final = "0000ae65-0000-1000-8000-00805f9b34fb"
SCAN_INTERVAL: Final = timedelta(seconds=2)  # Faster scanning for better responsiveness
DEVICE_TIMEOUT: Final = timedelta(seconds=5)  # Match Java code: 5 seconds timeout

# Signal Quality Thresholds (RSSI in dBm)
RSSI_EXCELLENT: Final = -50
RSSI_GOOD: Final = -70
RSSI_FAIR: Final = -85

# Configuration
CONF_MAC_ADDRESS: Final = "mac_address"
CONF_DEVICE_NAME: Final = "device_name"

# Sensor Types
SENSOR_TEMPERATURE: Final = "temperature"
SENSOR_TEMPERATURE_INT: Final = "temperature_int"
SENSOR_BATTERY_LEVEL: Final = "battery_level"
SENSOR_BATTERY_BARS: Final = "battery_bars"
SENSOR_RSSI: Final = "rssi"
SENSOR_CONNECTION_QUALITY: Final = "connection_quality"
BINARY_SENSOR_CONNECTED: Final = "connected"