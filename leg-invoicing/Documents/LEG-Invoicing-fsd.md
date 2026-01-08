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
