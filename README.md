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
- **Control** — stop the current session, adjust the current limit, pause/resume charging
- **Comprehensive monitoring** — per-phase current, power, energy, session tracking
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

### Sensors (11-12)

The `Current Request` sensor only appears when the firmware reports the value (Consumer Gateway mode). OCPP Translator mode omits the field and the integration skips creating the entity entirely.

| Entity | Key | Unit | Description |
|--------|-----|------|-------------|
| Current Request | `current_request` | A | Current requested by the EV (Consumer Gateway only) |
| Charging Current L1 | `charging_current_l1` | A | Phase 1 actual current |
| Charging Current L2 | `charging_current_l2` | A | Phase 2 actual current |
| Charging Current L3 | `charging_current_l3` | A | Phase 3 actual current |
| Charging Power | `charging_power` | W | Total charging power |
| kWh Delivered | `kwh_delivered` | kWh | Current session energy |
| Last Session Energy | `last_session_energy` | kWh | Previous session energy |
| Last Session Duration | `last_session_duration` | s | Previous session time |
| Current Session Duration | `current_session_duration` | s | Current session time |
| Charger State | `charger_state` | -- | Human-readable state (see below) |
| P14a Current Limit | `p14a_current_limit` | A | Effective grid-throttle limit when §14a curtailment is active |
| Product | `product` | -- | Diagnostic; firmware product family (e.g. `CONNECT Bridge`) |

### Binary Sensors (5)

| Entity | Key | Description |
|--------|-----|-------------|
| Session Active | `session_active` | Whether a charging session is active |
| P14a Enabled | `p14a_enabled` | Whether §14a grid-throttle support is configured on the device |
| P14a Active | `p14a_active` | Whether §14a curtailment is currently asserted |
| HeyCharge Backend Enabled | `heycharge_backend_enabled` | Cloud-backend feature flag — reports **off** until firmware emits this field in `/status` |
| HeyCharge Backend Connected | `heycharge_backend_connected` | Cloud-backend connectivity — reports **off** until firmware emits this field in `/status` |

### Switch (1)

| Entity | Key | Description |
|--------|-----|-------------|
| Pause Charging | `pause_charging` | ON = paused (0A sent to charger), OFF = normal |

### Number (1)

| Entity | Key | Range | Description |
|--------|-----|-------|-------------|
| Charging Current Limit | `current_limit` | 6-32 A | Maximum charging current |

### Buttons (1)

| Entity | Description |
|--------|-------------|
| End Session | Stop the current session |

> Starting a session from Home Assistant isn't currently exposed. The CONNECT firmware still has a `start_session` endpoint, but it's only useful when the wallbox needs an external trigger — most setups start charging by plugging in the EV. If you need a start-session button, file an issue with your use case.

## Charger States

The Charger State sensor reports a different vocabulary depending on which firmware mode the device is running in.

### Consumer Gateway (CONNECT MagicBox)

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

### OCPP Translator (CONNECT Bridge)

| State | Description |
|-------|-------------|
| Disconnected | No OCPP client connected (wallbox offline) |
| Preparing Connection | OCPP client connected but BootNotification not yet completed |
| Idle | Wallbox connected and idle |
| Starting | Remote- or local-start in flight, transaction not yet active |
| Charging | Active OCPP transaction (also surfaced briefly during WebSocket reconnect to avoid flicker) |
| Stopping | Stop in flight, transaction winding down |
| Faulted | Wallbox reported a fault |
| Updating | OCPP firmware update in progress |

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
  "admin_password_provisioned": true,
  "uptime_seconds": 12345,
  "boot_count": 7,
  "last_reset_reason": "POWERON"
}
```

`current_request` is omitted by OCPP Translator firmware — its absence signals the integration to skip creating the entity.

### GET /api/consumer_gateway/config

Returns device configuration (fetched once on startup).

```json
{
  "device_id": "A1B2C3D4",
  "charger_name": "Garage Charger",
  "manufacturer": "HeyCharge",
  "model": "GW-LITE",
  "product": "CONNECT Bridge",
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

### POST /api/consumer_gateway/end_session

```json
{}
```

> The firmware also exposes `POST /api/consumer_gateway/start_session` with a `{"type": "personal"|"company"}` payload, but this integration does not call it.

## Automation Examples

> Replace `<device>` below with your device's slug — that's the lower-cased, underscored name HA derived from the device title at setup. For a charger named "Garage" it's `garage`; for an Autel-vendor device it's likely `autel`. Find the exact slug in **Developer Tools → States**.

### Match Current Limit to Solar Excess

```yaml
automation:
  - alias: "Set charge current to track solar excess"
    trigger:
      - platform: state
        entity_id: sensor.solar_excess_power
    condition:
      - condition: state
        entity_id: binary_sensor.<device>_session_active
        state: "on"
    action:
      - service: number.set_value
        target:
          entity_id: number.<device>_charging_current_limit
        data:
          value: "{{ (states('sensor.solar_excess_power') | float / 230) | round(0) | int }}"
```

The integration doesn't expose a start-session button (the car normally starts charging by being plugged in), so solar-excess automations are usually current-limit adjustments rather than start triggers.

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
  - entity: button.<device>_end_session
```

## Troubleshooting

### Integration Can't Connect

- Verify the device is powered on and connected to your network
- Ensure the correct IP address/hostname is entered
- Confirm the device is running in a supported mode: a [CONNECT Bridge](https://heycharge.com/products/connect-bridge) is in **OCPP Translator** (mode 2) and a [CONNECT MagicBox](https://heycharge.com/products/consumer-gateway) is in **Consumer Gateway** (mode 6). Other modes don't expose the local API.
- Test the API directly: `curl -u admin:<password> http://<device-ip>/api/consumer_gateway/status` (HTTP Basic; username is fixed as `admin`, password is whatever was set on the device via WebUI or UART)

### Entities Not Updating

- Check Home Assistant logs for connection errors
- Verify network connectivity between HA and the device
- Try reloading the integration from **Settings > Devices & Services**

### Charger State Shows "Unknown"

The device hasn't yet observed the wallbox's state. On a [CONNECT MagicBox](https://heycharge.com/products/consumer-gateway), the state arrives in periodic DeviceStatus messages from the charger. On a [CONNECT Bridge](https://heycharge.com/products/connect-bridge), it derives from the OCPP client connection state. Either way, the state appears as soon as the wallbox connects.

## Technical Details

- **Polling interval**: 5 seconds (configurable in `const.py`)
- **Config caching**: Device config fetched once on startup, cached for the session
- **Timeout**: 10 seconds per HTTP request
- **Architecture**: Uses Home Assistant's `DataUpdateCoordinator` pattern
- **Session commands**: Deferred execution on the firmware side to prevent recursion
