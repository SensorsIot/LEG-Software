# LEG-MQTT-Simulator Functional Specification

## 1. Purpose

Generates realistic smart meter data for 4 simulated houses to complement the real House 1 data, enabling full LEG community simulation.

---

## 2. Scope

### 2.1 In Scope
- Simulated smart meter MQTT messages for houses 2-5
- Realistic energy consumption patterns
- PV production based on solar irradiance data
- Appliance simulation (EV charger, washing machine, dishwasher)
- Cumulative energy counter tracking (Ei/Eo)

### 2.2 Out of Scope
- Real smart meter integration (handled by actual hardware)
- Invoice generation (handled by LEG-Invoicing)
- Energy visualization (handled by LEG-Simulator)

---

## 3. Update Frequency

- **Interval:** 10 seconds
- **Topic:** `{MAC}/SENSOR` per house

---

## 4. Simulated Components

| Component | Details |
|-----------|---------|
| Base load | 500W day / 200W night (+/-20% random variation) |
| PV production | Based on Swiss solar irradiance data for Basel, scaled by kWp |
| Washing machine | 2 kW x 2 hours, once per day |
| Dishwasher | 1.5 kW x 1.5 hours, every 2 days |
| EV charger | 11 kW, per-house configuration (see 5.3) |

---

## 5. House Configuration

### 5.1 Overview Table

| House | Data Source | MAC Address | PV | EV | Washer | Dishwasher | Base Load |
|-------|-------------|-------------|-----|-----|--------|------------|-----------|
| 1 | Real meter | B0-81-84-25-22-5C | Yes | No | - | - | - |
| 2 | Simulated | AA-11-BB-22-CC-01 | 10 kWp | Yes (day) | Yes | Yes | Yes |
| 3 | Simulated | AA-11-BB-22-CC-02 | 5 kWp | Yes (night) | Yes | Yes | Yes |
| 4 | Simulated | AA-11-BB-22-CC-03 | None | No | Yes | Yes | Yes |
| 5 | Simulated | AA-11-BB-22-CC-04 | None | No | Yes | Yes | Yes |

### 5.2 Appliance Details per House

| House | PV System | EV Charger | Washing Machine | Dishwasher | Base Load |
|-------|-----------|------------|-----------------|------------|-----------|
| 2 | 10 kWp | 11 kW, 10:00-15:00, 2x/week | 2 kW, 2h, 1x/Day | 1.5 kW, 1.5h, every 2 days | 500W day / 200W night |
| 3 | 5kWp      | 11 kW, 22:00-03:00, 2x/week | 2 kW, 2h, 1x/Day | 1.5 kW, 1.5h, every 2 days | 500W day / 200W night |
| 4 | - | - | 2 kW, 2h, 1x/Day | 1.5 kW, 1.5h, every 2 days | 500W day / 200W night |
| 5 | - | - | 2 kW, 2h, 1x/Day | 1.5 kW, 1.5h, every 2 days | 500W day / 200W night |

### 5.3 EV Charging Patterns

| House | Charging Window | Duration | Energy per Session | Frequency |
|-------|-----------------|----------|-------------------|-----------|
| 2 | 8:00 - 15:00 (day) | ~4.5 hours | 25 kWh | daily |
| 3 | 22:00 - 03:00 (night) | ~4.5 hours | 50 kWh | 2x per week |

---

## 6. Time Simulation

The simulator operates with a **6-month time offset** to enable realistic summer PV production testing:

| Real Time | Simulated Time |
|-----------|----------------|
| January | July |
| February | August |

This ensures full PV production curves during winter testing.

---

## 7. Energy Accumulator Logic

The simulator maintains cumulative `Ei` and `Eo` counters per house:

```python
# Every 10 seconds:
net_power = base_load + appliances - pv_production

if net_power > 0:
    Ei += net_power * (10 / 3600)  # Importing (kWh)
else:
    Eo += abs(net_power) * (10 / 3600)  # Exporting (kWh)
```

---

## 8. State Storage (InfluxDB)

The simulator writes appliance state directly to InfluxDB at startup and on every change.

**Measurement:** `simulator_state`

| Field | Type | Description |
|-------|------|-------------|
| pv_kwp | float | PV system size |
| has_ev | int | 1 if house has EV, 0 otherwise |
| washing_active | int | 1 if washing machine running |
| dishwasher_active | int | 1 if dishwasher running |
| ev_active | int | 1 if EV charging |

**Tag:** house_id

---

## 9. MQTT Message Format

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

---

## 10. Deployment

| Parameter | Value |
|-----------|-------|
| Location | /root/LEG-Software/leg-mqtt-simulator/ |
| Broker | 10.0.0.1:1883 |
| Service | leg-mqtt-simulator.service |

---

## 11. Systemd Service

**Service file:** `/etc/systemd/system/leg-mqtt-simulator.service`

```ini
[Unit]
Description=LEG MQTT Simulator
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/LEG-Software/leg-mqtt-simulator
ExecStart=/usr/bin/python3 simulator.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Service Management

```bash
# Check status
systemctl status leg-mqtt-simulator

# Start/Stop/Restart
systemctl start leg-mqtt-simulator
systemctl stop leg-mqtt-simulator
systemctl restart leg-mqtt-simulator

# View logs
journalctl -u leg-mqtt-simulator -f

# Enable on boot
systemctl enable leg-mqtt-simulator
```
