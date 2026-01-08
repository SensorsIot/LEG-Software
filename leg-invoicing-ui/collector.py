"""
MQTT Collector Service for LEG-Invoicing

Subscribes to smart meter MQTT topics, calculates energy deltas,
applies tariffs, and stores all values in InfluxDB.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/leg-invoicing-collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = "10.0.0.1"
MQTT_PORT = 1883

# InfluxDB Configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "sE3jQga-sILQ2l1cdaFwbZIlAIlOYAEq99M9TQcIbasRlWKd5U553L5fOoOLGlwmn6gIHIjFaW8QLMfMRZghHQ=="
INFLUX_ORG = "LEG"
INFLUX_BUCKET = "energy"

# House configuration: MAC -> house_id mapping
HOUSE_CONFIG = {
    "B0-81-84-25-22-5C": 1,  # Real house
    "AA-11-BB-22-CC-01": 2,  # Simulated
    "AA-11-BB-22-CC-02": 3,  # Simulated
    "AA-11-BB-22-CC-03": 4,  # Simulated
    "AA-11-BB-22-CC-04": 5,  # Simulated
}

# Tariffs file path
TARIFFS_FILE = os.path.join(os.path.dirname(__file__), 'tariffs.json')

# Default tariffs (ct/kWh)
DEFAULT_TARIFFS = {
    'p_pv': 20.0,
    'p_con': 25.0,
    'p_grid_del': 6.0,
    'p_grid_con': 30.0,
}


class EnergyCollector:
    def __init__(self):
        # Store previous Ei/Eo values to calculate deltas
        self.previous_values: Dict[str, Dict[str, float]] = {}
        # Store current interval's data for all houses
        self.current_interval: Dict[str, Dict] = {}

        # Initialize InfluxDB client
        self.influx_client = InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        logger.info(f"Connected to InfluxDB at {INFLUX_URL}")

    def load_tariffs(self) -> Dict[str, float]:
        """Load current tariffs from file."""
        if os.path.exists(TARIFFS_FILE):
            with open(TARIFFS_FILE, 'r') as f:
                tariffs = json.load(f)
                if 'p_con' not in tariffs:
                    tariffs['p_con'] = (tariffs['p_pv'] + tariffs['p_grid_con']) / 2
                return tariffs
        return DEFAULT_TARIFFS.copy()

    def process_message(self, mac: str, payload: Dict):
        """Process incoming MQTT message and calculate energy delta."""
        if mac not in HOUSE_CONFIG:
            return

        house_id = HOUSE_CONFIG[mac]
        ei = payload.get('Ei', 0)
        eo = payload.get('Eo', 0)

        # Calculate deltas if we have previous values
        if mac in self.previous_values:
            prev = self.previous_values[mac]
            delta_ei = max(0, ei - prev['Ei'])  # Energy consumed
            delta_eo = max(0, eo - prev['Eo'])  # Energy exported (PV)

            self.current_interval[mac] = {
                'house_id': house_id,
                'delta_ei': delta_ei,
                'delta_eo': delta_eo,
            }

        # Update previous values
        self.previous_values[mac] = {'Ei': ei, 'Eo': eo}

    def store_interval_data(self):
        """Store all collected data for this interval to InfluxDB."""
        if not self.current_interval:
            return

        tariffs = self.load_tariffs()
        points = []

        total_consumption = 0
        total_production = 0

        # Create points for per-house data
        for mac, data in self.current_interval.items():
            delta_ei = data['delta_ei']
            delta_eo = data['delta_eo']

            # Calculate monetary values
            value_consumption = delta_ei * tariffs['p_con']
            value_pv_delivery = delta_eo * tariffs['p_pv']

            # House energy point
            point = Point("house_energy") \
                .tag("house_id", str(data['house_id'])) \
                .tag("mac", mac) \
                .field("delta_ei_kwh", delta_ei) \
                .field("delta_eo_kwh", delta_eo) \
                .field("value_consumption_ct", value_consumption) \
                .field("value_pv_delivery_ct", value_pv_delivery) \
                .field("tariff_p_con", tariffs['p_con']) \
                .field("tariff_p_pv", tariffs['p_pv'])

            points.append(point)

            total_consumption += delta_ei
            total_production += delta_eo

        # Calculate grid exchange
        net_energy = total_production - total_consumption

        if net_energy > 0:
            grid_export = net_energy
            grid_import = 0
        else:
            grid_export = 0
            grid_import = abs(net_energy)

        # Calculate monetary values for grid
        value_grid_export = grid_export * tariffs['p_grid_del']
        value_grid_import = grid_import * tariffs['p_grid_con']

        # Community energy point
        community_point = Point("community_energy") \
            .field("total_consumption_kwh", total_consumption) \
            .field("total_production_kwh", total_production) \
            .field("grid_import_kwh", grid_import) \
            .field("grid_export_kwh", grid_export) \
            .field("value_grid_import_ct", value_grid_import) \
            .field("value_grid_export_ct", value_grid_export) \
            .field("tariff_p_grid_con", tariffs['p_grid_con']) \
            .field("tariff_p_grid_del", tariffs['p_grid_del'])

        points.append(community_point)

        # Write all points to InfluxDB
        self.write_api.write(bucket=INFLUX_BUCKET, record=points)

        logger.info(
            f"Stored: cons={total_consumption:.6f}kWh, prod={total_production:.6f}kWh, "
            f"grid_in={grid_import:.6f}kWh ({value_grid_import:.2f}ct), "
            f"grid_out={grid_export:.6f}kWh ({value_grid_export:.2f}ct)"
        )

        # Clear current interval
        self.current_interval.clear()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe("+/SENSOR")
        logger.info("Subscribed to +/SENSOR")
    else:
        logger.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    try:
        mac = msg.topic.split('/')[0]
        payload = json.loads(msg.payload.decode())
        userdata['collector'].process_message(mac, payload)
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def main():
    import time

    collector = EnergyCollector()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={'collector': collector})
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    logger.info("Starting collector - storing data every 10 seconds to InfluxDB")

    try:
        while True:
            time.sleep(10)
            collector.store_interval_data()
    except KeyboardInterrupt:
        logger.info("Shutting down collector")
        client.loop_stop()
        client.disconnect()
        collector.influx_client.close()


if __name__ == '__main__':
    main()
