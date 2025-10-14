"""Config flow for DINUSO BLE Thermometer integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, TARGET_UUID, CONF_MAC_ADDRESS, CONF_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MAC_ADDRESS): str,
        vol.Required(CONF_DEVICE_NAME, default="DINUSO Thermometer"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DINUSO BLE Thermometer."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_devices = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            mac_address = user_input.get(CONF_MAC_ADDRESS, "").strip().upper()
            device_name = user_input[CONF_DEVICE_NAME]

            if mac_address:
                # Validate MAC address format
                if not self._is_valid_mac(mac_address):
                    errors[CONF_MAC_ADDRESS] = "invalid_mac"
                else:
                    # Check if device already configured
                    await self.async_set_unique_id(mac_address)
                    self._abort_if_unique_id_configured()

            if not errors:
                return self.async_create_entry(
                    title=device_name,
                    data={
                        CONF_MAC_ADDRESS: mac_address if mac_address else None,
                        CONF_DEVICE_NAME: device_name,
                    },
                )

        # Try to discover devices
        try:
            discovered = await self._async_discover_devices()
            if discovered:
                return await self.async_step_discovery(discovered)
        except Exception as err:
            _LOGGER.error("Failed to discover devices: %s", err)
            errors["base"] = "discovery_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_discovery(
        self, discovered_devices: dict[str, str]
    ) -> FlowResult:
        """Handle discovery step."""
        if len(discovered_devices) == 1:
            # Only one device found, use it directly
            mac_address = list(discovered_devices.keys())[0]
            device_name = discovered_devices[mac_address]
            
            await self.async_set_unique_id(mac_address)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_MAC_ADDRESS: mac_address,
                    CONF_DEVICE_NAME: device_name,
                },
            )

        # Multiple devices found, let user choose
        device_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(
                    {mac: f"{name} ({mac})" for mac, name in discovered_devices.items()}
                ),
                vol.Required(CONF_DEVICE_NAME, default="DINUSO Thermometer"): str,
            }
        )

        return self.async_show_form(
            step_id="discovery_select",
            data_schema=device_schema,
        )

    async def async_step_discovery_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection from discovery."""
        if user_input is not None:
            mac_address = user_input["device"]
            device_name = user_input[CONF_DEVICE_NAME]
            
            await self.async_set_unique_id(mac_address)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_MAC_ADDRESS: mac_address,
                    CONF_DEVICE_NAME: device_name,
                },
            )

        return self.async_abort(reason="no_device_selected")

    async def _async_discover_devices(self) -> dict[str, str]:
        """Discover DINUSO BLE devices."""
        discovered = {}

        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            if TARGET_UUID in (advertisement_data.service_data or {}):
                device_name = device.name or "DINUSO Thermometer"
                discovered[device.address.upper()] = device_name

        scanner = BleakScanner(detection_callback)
        
        try:
            await scanner.start()
            await asyncio.sleep(10)  # Scan for 10 seconds
        finally:
            await scanner.stop()

        return discovered

    def _is_valid_mac(self, mac: str) -> bool:
        """Validate MAC address format."""
        import re
        return bool(re.match(r"^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", mac.upper()))


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""