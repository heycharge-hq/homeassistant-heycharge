# HeyCharge Gateway Integration for Home Assistant

Custom integration providing native Home Assistant support for HeyCharge Gateway devices in Consumer Gateway mode. Communicates directly with the gateway via HTTP REST API -- no MQTT broker required.

## Features

- **Direct HTTP Connection** -- polls the gateway's REST API every 5 seconds
- **Zero Dependencies** -- no MQTT broker, no cloud account needed
- **Full Control** -- start/stop sessions, adjust current limits, pause charging
- **Comprehensive Monitoring** -- per-phase current, power, energy, session tracking
- **Company Car Mode** -- separate personal and company session tracking (when enabled in gateway settings)
- **Auto-Discovery** -- automatic device identification via the gateway config endpoint

## Installation

### Manual

```bash
cp -r custom_components/heycharge_gateway \
  /path/to/homeassistant/config/custom_components/
```

Restart Home Assistant after copying.

### HACS

1. Open HACS in your Home Assistant instance
2. Click the three-dot menu > **Custom repositories**
3. Add the repository URL and select **Integration** as the category
4. Search for "HeyCharge Gateway" and install
5. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration**
3. Search for **HeyCharge Gateway**
4. Enter the gateway's IP address or hostname (e.g. `192.168.1.100` or `heycharge-gw.local`)
5. Click **Submit**

The integration auto-discovers the device and creates all entities.

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
| HeyCharge Backend Enabled | `heycharge_backend_enabled` | Whether cloud backend is configured |
| HeyCharge Backend Connected | `heycharge_backend_connected` | Whether cloud backend is connected |

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

Returns all sensor values. Polled every 5 seconds.

```json
{
  "pause_charging": false,
  "session_enabled": true,
  "current_limit": 16.0,
  "current_request": 12.0,
  "charging_current_l1": 11.8,
  "charging_current_l2": 11.9,
  "charging_current_l3": 12.0,
  "charging_power": 8142.0,
  "kwh_delivered": 3.45,
  "last_session_energy": 12.8,
  "last_session_duration": 3600,
  "session_active": true,
  "current_session_duration": 1200,
  "charger_state": "Charging",
  "session_type": "personal",
  "heycharge_backend_enabled": true,
  "heycharge_backend_connected": true
}
```

### GET /api/consumer_gateway/config

Returns device configuration (fetched once on startup).

```json
{
  "device_id": "A1B2C3D4",
  "charger_name": "Garage Charger",
  "company_car_mode": false,
  "heycharge_backend_enabled": true,
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
        entity_id: binary_sensor.heycharge_gateway_charging
        state: "off"
    action:
      - service: button.press
        target:
          entity_id: button.heycharge_gateway_start_session
      - service: number.set_value
        target:
          entity_id: number.heycharge_gateway_current_limit
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
        entity_id: binary_sensor.heycharge_gateway_charging
        state: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.heycharge_gateway_pause_charging

  - alias: "Resume charging after peak hours"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.heycharge_gateway_pause_charging
```

### Basic Entities Card

```yaml
type: entities
title: EV Charging
entities:
  - entity: binary_sensor.heycharge_gateway_charging
  - entity: sensor.heycharge_gateway_charger_state
  - entity: sensor.heycharge_gateway_power
  - entity: sensor.heycharge_gateway_energy_delivered
  - entity: sensor.heycharge_gateway_current_l1
  - entity: sensor.heycharge_gateway_current_l2
  - entity: sensor.heycharge_gateway_current_l3
  - entity: number.heycharge_gateway_current_limit
  - entity: switch.heycharge_gateway_pause_charging
  - entity: button.heycharge_gateway_start_session
  - entity: button.heycharge_gateway_end_session
```

## Troubleshooting

### Integration Can't Connect

- Verify the gateway is powered on and connected to your network
- Ensure the correct IP address/hostname is entered
- Confirm the gateway is in **Consumer Gateway** mode (application mode 6)
- Test the API directly: `curl http://<gateway-ip>/api/consumer_gateway/status`

### Entities Not Updating

- Check Home Assistant logs for connection errors
- Verify network connectivity between HA and the gateway
- Try reloading the integration from **Settings > Devices & Services**

### Session Type Sensor Missing

The Session Type sensor only appears when **Company Car Mode** is enabled in the gateway firmware settings. This is normal if you don't need personal/company session tracking.

### Charger State Shows "Unknown"

This means the gateway hasn't received a status update from the charger yet. The state updates when the charger sends its periodic DeviceStatus messages.

## Technical Details

- **Polling interval**: 5 seconds (configurable in `const.py`)
- **Config caching**: Device config fetched once on startup, cached for the session
- **Timeout**: 10 seconds per HTTP request
- **Architecture**: Uses Home Assistant's `DataUpdateCoordinator` pattern
- **Session commands**: Deferred execution on the firmware side to prevent recursion
