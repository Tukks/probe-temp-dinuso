# DINUSO BLE Thermometer Home Assistant Integration

A custom Home Assistant integration for DINUSO BLE meat thermometer probes, supporting real-time temperature, battery, and connection quality sensors via Bluetooth LE advertisements.

---

## Features

- **Temperature (°C, integer and decimal)**
- **Battery level and bars**
- **Signal strength (RSSI) and connection quality**
- **Connection status (connected/disconnected)**

---

## Installation (via HACS)

1. **Add Custom Repository:**
   - Go to Home Assistant → Settings → Add-ons, Backups & Supervisor → HACS.
   - Click **"Integrations"** tab in HACS.
   - Click the **three dots** menu (top right) → **"Custom repositories"**.
   - Paste the repository URL:

     ```
     https://github.com/Tukks/probe-temp-dinuso
     ```

   - Set category as **"Integration"** and click **"Add"**.

2. **Install the Integration:**
   - Search for **"DINUSO BLE Thermometer"** in HACS Integrations.
   - Click **"Install"**.

3. **Restart Home Assistant:**
   - Go to **Developer Tools → Restart** (or Settings → System → Restart).

4. **Add the Integration:**
   - Go to **Settings → Devices & Services → Add Integration**.
   - Search for **DINUSO BLE Thermometer**.
   - Follow the setup wizard (manual MAC address entry).

---

## Manual Installation (Optional)

1. Copy the `custom_components/dinuso_ble` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via Settings as above.

---

## Requirements

- Home Assistant OS or Supervised with Bluetooth/BLE support
- [HACS (Home Assistant Community Store)](https://hacs.xyz/)
- Python 3.10+ (Home Assistant Core compatibility)

---

## Support

- Issues & requests: [GitHub Issues](https://github.com/giuseppe-lapenta_monline/homeassistant-dinuso-ble/issues)
- For more info, see [Home Assistant Custom Integration Docs](https://developers.home-assistant.io/docs/creating_integration_manifest/)

---

## License

MIT License