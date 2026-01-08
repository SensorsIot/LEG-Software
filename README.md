# ⚡ LEG-Simulator

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.15+-00d4aa?logo=plotly&logoColor=white)](https://dash.plotly.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

## 🎯 Purpose

LEG-Simulator provides **real-time visualization of electrical energy flows** within a Local Energy Grid (LEG) - a small community of houses with photovoltaic (PV) systems.

It answers the question: *"What is happening right now with energy in our community?"*

> ⚠️ This is a **descriptive simulator**, not an optimizer. It shows current state, not recommendations.

## ✨ What You See

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   House 1   │────▶│  Community  │────▶│  External   │
│   House 2   │────▶│     Bus     │◀────│    Grid     │
│   House N   │────▶│             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
     ☀️ PV              ⚡ Balance           🔌 Import/Export
     🔌 Load
```

- 🏠 **Houses**: Each with solar panels and consumption
- ☀️ **PV Production**: Simulated with realistic daily variation
- 🔌 **Loads**: Base consumption + random flexible loads (EV, appliances)
- 🔄 **Energy Flows**: Visualized in real-time with colored edges
- 📊 **Grid Exchange**: Community surplus/deficit with external grid

## 🎨 Visual Indicators

| Color | Meaning |
|-------|---------|
| 🟢 Green | Energy export (surplus) |
| 🟠 Orange | Energy import (deficit) |
| ⚪ Grey | No significant flow |
| **Thickness** | Proportional to power (W) |

---

## 🚀 Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

🌐 Open http://localhost:8050

## ⚙️ Configuration

Edit `config.yaml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `houses` | Number of houses | 5 |
| `update_interval_ms` | Refresh rate (ms) | 1000 |
| `pv_variation` | Solar variation | enabled |
| `flex_load_probability` | Flex load chance | 0.1 |

## 📁 Files

| File | Purpose |
|------|---------|
| `app.py` | Dash entry point |
| `model.py` | Energy model logic |
| `simulation.py` | Simulation loop |
| `layout.py` | Graph visualization |
| `config.yaml` | Settings |

## 🔮 Future Extensions

- 🔋 Battery storage
- 💰 Price signals
- 🤖 Optimization layer

---

<p align="center">Made with ⚡ for the energy community</p>
