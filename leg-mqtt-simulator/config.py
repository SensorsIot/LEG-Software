"""House configurations for LEG MQTT simulator."""

MQTT_BROKER = "10.0.0.1"
MQTT_PORT = 1883
UPDATE_INTERVAL = 10  # seconds

# House configurations
HOUSES = [
    {
        "id": 2,
        "mac": "AA-11-BB-22-CC-01",
        "smid": "SIM00002",
        "pv_kwp": 10.0,
        "has_ev": True,
        "ev_schedule": "day",  # 10:00-15:00
    },
    {
        "id": 3,
        "mac": "AA-11-BB-22-CC-02",
        "smid": "SIM00003",
        "pv_kwp": 20.0,
        "has_ev": True,
        "ev_schedule": "night",  # 22:00-03:00
    },
    {
        "id": 4,
        "mac": "AA-11-BB-22-CC-03",
        "smid": "SIM00004",
        "pv_kwp": 0.0,
        "has_ev": False,
        "ev_schedule": None,
    },
    {
        "id": 5,
        "mac": "AA-11-BB-22-CC-04",
        "smid": "SIM00005",
        "pv_kwp": 0.0,
        "has_ev": False,
        "ev_schedule": None,
    },
]

# Load parameters
BASE_LOAD_DAY_W = 500      # 06:00-22:00
BASE_LOAD_NIGHT_W = 200    # 22:00-06:00
BASE_LOAD_VARIATION = 0.2  # ±20%

# Appliance parameters
WASHING_MACHINE_KW = 2.0
WASHING_MACHINE_HOURS = 2.0
WASHING_FREQUENCY_DAYS = 7  # 1x per week

DISHWASHER_KW = 1.5
DISHWASHER_HOURS = 1.5
DISHWASHER_FREQUENCY_DAYS = 2  # every 2 days

EV_CHARGER_KW = 11.0
EV_CHARGE_KWH = 50.0  # per session
EV_FREQUENCY_DAYS = 3.5  # 2x per week

# Persistence file for Ei/Eo counters
STATE_FILE = "/root/LEG-Software/leg-mqtt-simulator/state.json"
