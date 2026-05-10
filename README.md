# HeyCharge CONNECT — Home Assistant Integration

Custom integration providing native Home Assistant support for the [**HeyCharge CONNECT**](https://heycharge.com/) product line. Talks directly to the device over LAN, no MQTT broker or cloud account required.

| Product | What it does | Firmware mode |
|--|--|--|
| [**CONNECT Bridge**](https://heycharge.com/products/connect-bridge) | Adapts any OCPP wallbox to the HeyCharge platform — AC or DC | OCPP Translator |
| [**CONNECT MagicBox**](https://heycharge.com/products/consumer-gateway) | Retrofit adapter that adds smart charging to any OCPP wallbox | Consumer Gateway |

Both expose the same local HTTP REST API at `/api/consumer_gateway/*`, so this single integration covers both products.

## Features

- **Direct HTTP connection** — polls the device's REST API every 5 seconds
- **Zeroconf auto-discovery** — devices advertising `_heycharge._tcp` show up under **Settings → Devices & Services → Discovered**
- **Full control** — start/stop sessions, adjust current limit, pause charging
- **Comprehensive monitoring** — per-phase current, power, energy, session tracking
- **Company car mode** — separate personal and company session tracking when enabled on the device
- **§14a / P14a support** — exposes utility throttle state and effective limit when the device implements §14a (BNetzA grid-throttle support)

## Installation

### Manual

```bash
cp -r custom_components/heycharge \
  /path/to/homeassistant/config/custom_components/
```

Restart Home Assistant after copying.

### HACS

1. Open HACS in your Home Assistant instance.
2. Click the three-dot menu in the top-right → **Custom repositories**.
3. Add the URL `https://github.com/heycharge-hq/homeassistant-heycharge` and pick **Integration** as the type.
4. Click **Download** on the new "HeyCharge CONNECT" entry.
5. Restart Home Assistant.

## Configuration

If the device is on the same LAN, it should appear automatically under **Settings → Devices & Services → Discovered** (zeroconf, service type `_heycharge._tcp`). Otherwise add it manually:

1. **Settings → Devices & Services → + Add Integration**.
2. Search for **HeyCharge CONNECT**.
3. Enter the device's IP or hostname (e.g. `192.168.1.100` or `gw-garage.local`).
4. **Submit**.

The integration fetches the device's config endpoint to identify it and create entities.

## Entities

### Sensors (10-11)

| Entity | Key | Unit | Description |
|--------|-----|------|-------------|
| Current Request | `current_request` | A | Current requested by the EV |
| Current L1 | `charging_current_l1` | A | Phase 1 actual current |
| Current L2 | `charging_current_l2` | A | Phase 2 actual current |
| Current L3 | `charging_current_l3` | A | Phase 3 actual current |
| Power | `charging_power` | W | Total charging power |
| Energy Delivered | `kwh_delivered` | kWh | Current session energy |
| Last Session Energy | `last_session_energy` | kWh | Previous session energy |
| Last Session Duration | `last_session_duration` | s | Previous session time |
| Session Duration | `current_session_duration` | s | Current session time |
| Charger State | `charger_state` | -- | Human-readable state (Idle, Charging, etc.) |
| Session Type | `session_type` | -- | personal/company/none (only when company car mode enabled) |

### Binary Sensors (3)

| Entity | Key | Description |
|--------|-----|-------------|
| Charging | `session_active` | Whether a charging session is active |
| HeyCharge Backend Enabled | `heycharge_backend_enabled` | Whether cloud backend is configured (currently `Unavailable` — pending firmware support) |
| HeyCharge Backend Connected | `heycharge_backend_connected` | Whether cloud backend is connected (currently `Unavailable` — pending firmware support) |

### Switch (1)

| Entity | Key | Description |
|--------|-----|-------------|
| Pause Charging | `pause_charging` | ON = paused (0A sent to charger), OFF = normal |

### Number (1)

| Entity | Key | Range | Description |
|--------|-----|-------|-------------|
| Current Limit | `current_limit` | 6-32 A | Maximum charging current |

### Buttons (2-3)

When company car mode is **disabled**:

| Entity | Description |
|--------|-------------|
| Start Session | Start a personal charging session |
| End Session | Stop the current session |

When company car mode is **enabled**:

| Entity | Description |
|--------|-------------|
| Start Session (Personal) | Start a personal session |
| Start Session (Company) | Start a company session |
| End Session | Stop the current session |

## Charger States

The Charger State sensor reports these values:

| State | Description |
|-------|-------------|
| Unknown | Initial state before first status update |
| Not Onboarded | Charger not yet provisioned |
| Onboarding | Charger provisioning in progress |
| Idle | Ready, no session active |
| Initiated | Session starting, waiting for EV |
| Charging | Actively delivering energy |
| Charging Stopped | Session ended, EV still connected |
| Charging Stop Initiated | Stop command sent, winding down |
| Fatal Error | Hardware or communication error |
| Boot | Charger is booting up |
| Host OTA | Firmware update in progress |

## REST API Reference

The integration communicates with these firmware endpoints:

### GET /api/consumer_gateway/status

Returns all sensor values. Polled every 5 seconds. Authenticated with HTTP Basic.

```json
{
  "pause_charging": false,
  "pause_charging_mqtt": false,
  "pause_charging_modbus": false,
  "session_active": true,
  "current_limit": 16.0,
  "current_request": 12.0,
  "charging_current_l1": 11.8,
  "charging_current_l2": 11.9,
  "charging_current_l3": 12.0,
  "charging_power": 8142.0,
  "kwh_delivered": 3.45,
  "last_session_energy": 12.8,
  "last_session_duration": 3600,
  "current_session_duration": 1200,
  "charger_state": "Charging",
  "p14a_enabled": false,
  "p14a_active": false,
  "p14a_current_limit": 0.0,
  "admin_password_provisioned": true
}
```

### GET /api/consumer_gateway/config

Returns device configuration (fetched once on startup).

```json
{
  "device_id": "A1B2C3D4",
  "charger_name": "Garage Charger",
  "manufacturer": "HeyCharge",
  "model": "GW-LITE",
  "fw_version": "0.5.0",
  "build_string": "...",
  "company_car_mode": false,
  "min_current": 6,
  "max_current": 32
}
```

### POST /api/consumer_gateway/pause

```json
{"paused": true}
```

### POST /api/consumer_gateway/current_limit

```json
{"limit": 16.0}
```
Accepted range: 6-32 A.

### POST /api/consumer_gateway/start_session

```json
{"type": "personal"}
```
Type can be `"personal"` or `"company"`.

### POST /api/consumer_gateway/end_session

```json
{}
```

## Automation Examples

> Replace `<device>` below with your device's slug — that's the lower-cased, underscored name HA derived from the device title at setup. For a charger named "Garage" it's `garage`; for an Autel-vendor device it's likely `autel`. Find the exact slug in **Developer Tools → States**.

### Start Charging with Solar Excess

```yaml
automation:
  - alias: "Charge car with solar excess"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_excess_power
        above: 3000
    condition:
      - condition: state
        entity_id: binary_sensor.<device>_session_active
        state: "off"
    action:
      - service: button.press
        target:
          entity_id: button.<device>_start_session_personal
      - service: number.set_value
        target:
          entity_id: number.<device>_charging_current_limit
        data:
          value: 16
```

### Pause During Peak Hours

```yaml
automation:
  - alias: "Pause charging during peak hours"
    trigger:
      - platform: time
        at: "17:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.<device>_session_active
        state: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.<device>_pause_charging

  - alias: "Resume charging after peak hours"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.<device>_pause_charging
```

### Basic Entities Card

```yaml
type: entities
title: EV Charging
entities:
  - entity: binary_sensor.<device>_session_active
  - entity: sensor.<device>_charger_state
  - entity: sensor.<device>_charging_power
  - entity: sensor.<device>_kwh_delivered
  - entity: sensor.<device>_charging_current_l1
  - entity: sensor.<device>_charging_current_l2
  - entity: sensor.<device>_charging_current_l3
  - entity: number.<device>_charging_current_limit
  - entity: switch.<device>_pause_charging
  - entity: button.<device>_start_session_personal
  - entity: button.<device>_end_session
```

## Troubleshooting

### Integration Can't Connect

- Verify the device is powered on and connected to your network
- Ensure the correct IP address/hostname is entered
- Confirm the device is running in a supported mode: a [CONNECT Bridge](https://heycharge.com/products/connect-bridge) is in **OCPP Translator** (mode 2) and a [CONNECT MagicBox](https://heycharge.com/products/consumer-gateway) is in **Consumer Gateway** (mode 6). Other modes don't expose the local API.
- Test the API directly: `curl -u <user>:<pass> http://<device-ip>/api/consumer_gateway/status` (the local API requires HTTP Basic auth)

### Entities Not Updating

- Check Home Assistant logs for connection errors
- Verify network connectivity between HA and the device
- Try reloading the integration from **Settings > Devices & Services**

### Session Type Sensor Missing

The Session Type sensor only appears when **Company Car Mode** is enabled in the device's firmware settings. This is normal if you don't need personal/company session tracking.

### Charger State Shows "Unknown"

The device hasn't yet observed the wallbox's state. On a [CONNECT MagicBox](https://heycharge.com/products/consumer-gateway), the state arrives in periodic DeviceStatus messages from the charger. On a [CONNECT Bridge](https://heycharge.com/products/connect-bridge), it derives from the OCPP client connection state. Either way, the state appears as soon as the wallbox connects.

## Technical Details

- **Polling interval**: 5 seconds (configurable in `const.py`)
- **Config caching**: Device config fetched once on startup, cached for the session
- **Timeout**: 10 seconds per HTTP request
- **Architecture**: Uses Home Assistant's `DataUpdateCoordinator` pattern
- **Session commands**: Deferred execution on the firmware side to prevent recursion
