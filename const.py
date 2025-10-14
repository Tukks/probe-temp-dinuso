from datetime import timedelta
from typing import Final

DOMAIN: Final = "dinuso_ble"
MANUFACTURER: Final = "DINUSO"
MODEL: Final = "BLE Meat Thermometer"

TARGET_UUID: Final = "0000ae65-0000-1000-8000-00805f9b34fb"
SCAN_INTERVAL: Final = timedelta(seconds=2)
DEVICE_TIMEOUT: Final = timedelta(seconds=40)

RSSI_EXCELLENT: Final = -50
RSSI_GOOD: Final = -70
RSSI_FAIR: Final = -85

CONF_MAC_ADDRESS: Final = "mac_address"
CONF_DEVICE_NAME: Final = "device_name"

SENSOR_TEMPERATURE: Final = "temperature"
SENSOR_TEMPERATURE_INT: Final = "temperature_int"
SENSOR_BATTERY_LEVEL: Final = "battery_level"
SENSOR_BATTERY_BARS: Final = "battery_bars"
SENSOR_RSSI: Final = "rssi"
SENSOR_CONNECTION_QUALITY: Final = "connection_quality"
BINARY_SENSOR_CONNECTED: Final = "connected"