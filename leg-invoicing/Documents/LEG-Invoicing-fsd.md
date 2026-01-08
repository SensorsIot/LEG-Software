# LEG-Invoicing Functional Specification

## 1. Purpose

LEG-Invoicing provides billing and invoicing functionality for Local Energy Grid (LEG) communities. It generates invoices based on energy flows between houses, the community, and the external grid.

---

## 2. Scope

### 2.1 In Scope
- Invoice generation for community members
- Energy consumption/production tracking
- Pricing calculations based on LEG-Simulator pricing model
- Invoice export (PDF, CSV)
- Settlement period management

### 2.2 Out of Scope
- Real-time energy flow visualization (handled by LEG-Simulator)
- Payment processing
- Bank integration
- Tax calculations

---

## 3. Data Model

### 3.1 Invoice

```json
{
  "invoice_id": "INV-2026-001",
  "house_id": "house_1",
  "period_start": "2026-01-01T00:00:00Z",
  "period_end": "2026-01-31T23:59:59Z",
  "energy_exported_kwh": 450.5,
  "energy_imported_kwh": 120.3,
  "export_revenue_ct": 9010,
  "import_cost_ct": 3007.5,
  "net_amount_ct": 6002.5,
  "status": "pending"
}
```

### 3.2 Settlement Period

```json
{
  "period_id": "2026-01",
  "start": "2026-01-01T00:00:00Z",
  "end": "2026-01-31T23:59:59Z",
  "status": "open",
  "invoices": []
}
```

---

## 4. Pricing Integration

Uses the same pricing model as LEG-Simulator (Section 12.3):

| Parameter | Description | Default |
|-----------|-------------|---------|
| p_pv | PV Delivery (house sells to community) | 20 ct/kWh |
| p_con | House Consumption (house buys from community) | 25 ct/kWh |
| p_grid_del | Grid Delivery (community sells to grid) | 6 ct/kWh |
| p_grid_con | Grid Consumption (community buys from grid) | 30 ct/kWh |

---

## 5. Technical Architecture

### 5.1 Runtime Environment
- Python 3.10+
- Shared deployment with LEG-Simulator

### 5.2 Dependencies
- dash (web interface)
- pandas (data processing)
- weasyprint or reportlab (PDF generation)

---

## 6. Deployment

| Component | Value |
|-----------|-------|
| Server | LEG-Configurator |
| URL | https://provision.dhamstack.com:TBD |
| Path | /root/LEG-Software/leg-invoicing/ |

---

## 7. Future Extensions

- Integration with smart meter data
- Automated invoice delivery via email
- Multi-community support

---

## 8. MQTT Data Source

### 8.1 Overview

LEG-Invoicing receives energy metering data from smart meters via MQTT. One real smart meter provides data for House 1, while houses 2-5 are simulated by the `leg-mqtt-simulator` component.

### 8.2 MQTT Broker

| Parameter | Value |
|-----------|-------|
| Host | provision.dhamstack.com |
| Port (VPN) | 1883 (10.0.0.1, anonymous) |
| Port (Public) | 8883 (TLS, password auth) |
| Topic Pattern | `{MAC}/SENSOR` |

### 8.3 Message Format

```json
{
  "SMid": "60222760",
  "Pi": 1.047,
  "Po": 0.000,
  "I1": 0.392,
  "I2": 0.054,
  "I3": 0.096,
  "Ei": 4619.712,
  "Eo": 14089.216,
  "Q5": 18.862,
  "Q6": 12.491,
  "Q7": 1932.711,
  "Q8": 3664.889,
  "ts": 12589
}
```

**Key Fields:**
| Field | Description | Unit |
|-------|-------------|------|
| Pi | Instantaneous power IN (consumption) | kW |
| Po | Instantaneous power OUT (PV export) | kW |
| Ei | Cumulative energy IN (ever-increasing total) | kWh |
| Eo | Cumulative energy OUT (ever-increasing total) | kWh |
| ts | Timestamp (incrementing seconds) | s |

**Invoice Calculation:** Uses delta between consecutive `Ei`/`Eo` values over the settlement period.

### 8.4 House Configuration

| House | MAC Address | Data Source | PV | EV |
|-------|-------------|-------------|-----|-----|
| 1 | B0-81-84-25-22-5C | Real smart meter | Yes | No |
| 2 | AA-11-BB-22-CC-01 | Simulated | 10 kWp | Yes (day) |
| 3 | AA-11-BB-22-CC-02 | Simulated | 20 kWp | Yes (night) |
| 4 | AA-11-BB-22-CC-03 | Simulated | None | No |
| 5 | AA-11-BB-22-CC-04 | Simulated | None | No |

---

## 9. MQTT Simulator (leg-mqtt-simulator)

### 9.1 Purpose

Generates realistic smart meter data for 4 simulated houses to complement the real House 1 data, enabling full LEG community simulation.

### 9.2 Update Frequency

- **Interval:** 10 seconds
- **Topic:** `{MAC}/SENSOR` per house

### 9.3 Load Profiles

#### 9.3.1 Base Load
| Time | Power |
|------|-------|
| 06:00 - 22:00 | 500W ± random variation |
| 22:00 - 06:00 | 200W ± random variation |

#### 9.3.2 Appliances

| Appliance | Power | Duration | Frequency |
|-----------|-------|----------|-----------|
| Washing Machine | 2 kW | 2 hours | 1× per week per house |
| Dishwasher | 1.5 kW | 1.5 hours | Every 2 days per house |
| EV Charger | 11 kW | ~4.5 hours (50 kWh) | 2× per week (House 2: day, House 3: night) |

#### 9.3.3 PV Production

- **Data Source:** Swiss solar irradiance data for Basel, July
- **Peak Hours:** ~06:00 - 20:00, maximum ~11:00 - 15:00
- **Scaling:** Proportional to system size (10 kWp or 20 kWp)
- **Cloud Variation:** Random ±20% fluctuation

### 9.4 Energy Accumulator Logic

The simulator maintains cumulative `Ei` and `Eo` counters per house:

```python
# Every 10 seconds:
energy_delta = power_kw * (10 / 3600)  # kWh per 10s interval

net_power = base_load + appliances - pv_production

if net_power > 0:
    Ei += net_power * (10 / 3600)  # Importing
else:
    Eo += abs(net_power) * (10 / 3600)  # Exporting
```

### 9.5 Deployment

| Parameter | Value |
|-----------|-------|
| Location | /root/LEG-Software/leg-mqtt-simulator/ |
| Broker | localhost:1883 (10.0.0.1) |
| Service | systemd or nohup |

### 9.6 House Simulation Summary

```
House 2 (10 kWp PV, EV day):
├── Base: 500W day / 200W night
├── PV: 0-10kW (peak ~12:00)
├── EV: 11kW × 4.5h, 2×/week, 10:00-15:00
├── Dishwasher: 1.5kW × 1.5h, every 2 days
└── Washing: 2kW × 2h, 1×/week

House 3 (20 kWp PV, EV night):
├── Base: 500W day / 200W night
├── PV: 0-20kW (peak ~12:00)
├── EV: 11kW × 4.5h, 2×/week, 22:00-03:00
├── Dishwasher: 1.5kW × 1.5h, every 2 days
└── Washing: 2kW × 2h, 1×/week

House 4 (No PV, No EV):
├── Base: 500W day / 200W night
├── Dishwasher: 1.5kW × 1.5h, every 2 days
└── Washing: 2kW × 2h, 1×/week

House 5 (No PV, No EV):
├── Base: 500W day / 200W night
├── Dishwasher: 1.5kW × 1.5h, every 2 days
└── Washing: 2kW × 2h, 1×/week
```

### 9.7 Time Simulation

The simulator operates with a **6-month time offset** to enable realistic summer PV production testing:

```
Real time:      January 8, 14:30
Simulated time: July 8, 14:30
```

This ensures:
- Full PV production curves during winter testing
- Accurate summer load patterns
- Realistic energy export scenarios

**Implementation:**
```python
from dateutil.relativedelta import relativedelta
simulated_time = datetime.now() + relativedelta(months=6)
```

---

## 10. Data Storage (InfluxDB)

### 10.1 Overview

Energy data is stored in InfluxDB, a time-series database optimized for high-volume measurements.

### 10.2 Connection Details

| Parameter | Value |
|-----------|-------|
| Server | provision.dhamstack.com |
| Port (Internal) | 8086 |
| Port (External/HTTPS) | 8087 |
| Organization | LEG |
| Bucket | energy |
| User | admin |

### 10.3 Measurements

#### house_energy (per-house data)

| Field | Type | Description |
|-------|------|-------------|
| delta_ei_kwh | float | Energy consumed this interval |
| delta_eo_kwh | float | Energy exported this interval |
| value_consumption_ct | float | delta_ei × p_con |
| value_pv_delivery_ct | float | delta_eo × p_pv |
| tariff_p_con | float | Applied consumption tariff |
| tariff_p_pv | float | Applied PV delivery tariff |

**Tags:** house_id, mac

#### community_energy (aggregated data)

| Field | Type | Description |
|-------|------|-------------|
| total_consumption_kwh | float | Sum of all house consumption |
| total_production_kwh | float | Sum of all house production |
| grid_import_kwh | float | Energy bought from grid |
| grid_export_kwh | float | Energy sold to grid |
| value_grid_import_ct | float | grid_import × p_grid_con |
| value_grid_export_ct | float | grid_export × p_grid_del |
| tariff_p_grid_con | float | Applied grid consumption tariff |
| tariff_p_grid_del | float | Applied grid delivery tariff |

### 10.4 Data Flow

```
MQTT Messages → Collector → InfluxDB
     ↓              ↓
  Ei/Eo        Calculate deltas
  values       Apply tariffs
               Store every 10s
```

---

## 11. Configuration

### 11.1 Overview

All services use a centralized YAML configuration file (`config.yaml`). A template is provided in `config.example.yaml`.

### 11.2 Configuration File Structure

```yaml
mqtt:
  broker: "provision.dhamstack.com"
  port: 8883
  use_tls: true
  username: "..."
  password: "..."

influxdb:
  url: "https://provision.dhamstack.com:8087"
  token: "..."
  org: "LEG"
  bucket: "energy"

houses:
  "B0-81-84-25-22-5C":
    id: 1
    name: "House 1"
    type: "real"
  # ... more houses

tariffs:
  p_pv: 20.0
  p_grid_del: 6.0
  p_grid_con: 30.0

collector:
  interval: 10

web:
  host: "0.0.0.0"
  port: 8060

logging:
  level: "INFO"
  file: null
```

### 11.3 Environment-Specific Settings

| Setting | Local Development | Remote Server |
|---------|-------------------|---------------|
| MQTT Broker | provision.dhamstack.com:8883 | 10.0.0.1:1883 |
| MQTT TLS | Yes | No |
| InfluxDB URL | https://provision...:8087 | http://localhost:8086 |

### 11.4 Git Strategy

- `config.example.yaml` - Committed (template)
- `config.yaml` - Ignored (contains secrets)

---

## 12. Development Environment

### 12.1 Local Development

Development is performed on the local machine with deployment to the remote server.

| Component | Local Path |
|-----------|------------|
| Repository | /home/energymanagement/LEG-Software/ |
| Invoicing UI | leg-invoicing-ui/ |
| MQTT Simulator | leg-mqtt-simulator/ |
| Documentation | leg-invoicing/Documents/ |

### 12.2 Deployment Workflow

```
1. Edit code locally
2. git commit && git push
3. SSH to remote: git pull
4. Restart services
```

### 12.3 Remote Server

| Service | URL | Port |
|---------|-----|------|
| Tariff UI | https://provision.dhamstack.com:8052 | 8052 |
| InfluxDB | https://provision.dhamstack.com:8087 | 8087 |
| LEG-Simulator | https://provision.dhamstack.com:8051 | 8051 |
| Provisioning | https://provision.dhamstack.com:5000 | 5000 |

---

## 13. Tariff UI (leg-invoicing-ui)

### 13.1 Purpose

Web interface for managing energy tariffs used in invoice calculations.

### 13.2 Features

- Input table for configurable tariffs (p_pv, p_grid_del, p_grid_con)
- Auto-calculated house tariff: p_con = (p_pv + p_grid_con) / 2
- REST API for tariff management
- Real-time updates via JavaScript

### 13.3 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | Tariff management UI |
| /api/tariffs | GET | Get current tariffs |
| /api/tariffs | POST | Update tariffs |

### 13.4 Technology Stack

- Flask (Python web framework)
- HTML/CSS/JavaScript frontend
- tariffs.json (persistent storage)
