"""
LEG Invoicing Web UI

Provides tariff management and energy data access via REST API.
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta

import yaml
from influxdb_client import InfluxDBClient

app = Flask(__name__)

# Load configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

TARIFFS_FILE = os.path.join(os.path.dirname(__file__), 'tariffs.json')
DEFAULT_TARIFFS = config.get('tariffs', {
    'p_pv': 20.0,
    'p_grid_del': 6.0,
    'p_grid_con': 30.0,
})

# InfluxDB client
influx_config = config.get('influxdb', {})
influx_client = InfluxDBClient(
    url=influx_config.get('url', 'http://localhost:8086'),
    token=influx_config.get('token', ''),
    org=influx_config.get('org', 'LEG'),
    verify_ssl=False
)
query_api = influx_client.query_api()
INFLUX_BUCKET = influx_config.get('bucket', 'energy')


def load_tariffs():
    if os.path.exists(TARIFFS_FILE):
        with open(TARIFFS_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_TARIFFS.copy()


def save_tariffs(tariffs):
    with open(TARIFFS_FILE, 'w') as f:
        json.dump(tariffs, f, indent=2)


def calculate_house_tariff(tariffs):
    """Calculate house consumption tariff (p_con) based on other tariffs."""
    p_con = (tariffs['p_pv'] + tariffs['p_grid_con']) / 2
    return round(p_con, 2)


@app.route('/')
def index():
    tariffs = load_tariffs()
    tariffs['p_con'] = calculate_house_tariff(tariffs)
    return render_template('index.html', tariffs=tariffs)


@app.route('/api/tariffs', methods=['GET'])
def get_tariffs():
    tariffs = load_tariffs()
    tariffs['p_con'] = calculate_house_tariff(tariffs)
    return jsonify(tariffs)


@app.route('/api/tariffs', methods=['POST'])
def update_tariffs():
    data = request.json
    tariffs = {
        'p_pv': float(data.get('p_pv', DEFAULT_TARIFFS['p_pv'])),
        'p_grid_del': float(data.get('p_grid_del', DEFAULT_TARIFFS['p_grid_del'])),
        'p_grid_con': float(data.get('p_grid_con', DEFAULT_TARIFFS['p_grid_con'])),
    }
    save_tariffs(tariffs)
    tariffs['p_con'] = calculate_house_tariff(tariffs)
    return jsonify({'status': 'success', 'tariffs': tariffs})


@app.route('/api/energy/summary', methods=['GET'])
def get_energy_summary():
    """Get energy summary for all houses over a time period."""
    hours = request.args.get('hours', 24, type=int)

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "house_energy")
      |> group(columns: ["house_id", "_field"])
      |> sum()
    '''

    try:
        result = query_api.query(query)

        houses = {}
        for table in result:
            for record in table.records:
                house_id = record.values.get('house_id', 'unknown')
                field = record.get_field()
                value = record.get_value()

                if house_id not in houses:
                    houses[house_id] = {}
                houses[house_id][field] = round(value, 4) if value else 0

        return jsonify({
            'status': 'success',
            'period_hours': hours,
            'houses': houses
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/energy/community', methods=['GET'])
def get_community_energy():
    """Get community-level energy data."""
    hours = request.args.get('hours', 24, type=int)

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "community_energy")
      |> group(columns: ["_field"])
      |> sum()
    '''

    try:
        result = query_api.query(query)

        data = {}
        for table in result:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                data[field] = round(value, 4) if value else 0

        return jsonify({
            'status': 'success',
            'period_hours': hours,
            'community': data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/energy/house/<house_id>', methods=['GET'])
def get_house_energy(house_id):
    """Get energy data for a specific house."""
    hours = request.args.get('hours', 24, type=int)

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "house_energy")
      |> filter(fn: (r) => r.house_id == "{house_id}")
      |> group(columns: ["_field"])
      |> sum()
    '''

    try:
        result = query_api.query(query)

        data = {}
        for table in result:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                data[field] = round(value, 4) if value else 0

        return jsonify({
            'status': 'success',
            'house_id': house_id,
            'period_hours': hours,
            'energy': data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/energy/timeseries', methods=['GET'])
def get_energy_timeseries():
    """Get time series data for charts."""
    hours = request.args.get('hours', 1, type=int)
    measurement = request.args.get('measurement', 'community_energy')
    field = request.args.get('field', 'total_consumption_kwh')

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{hours}h)
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => r._field == "{field}")
      |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)
    '''

    try:
        result = query_api.query(query)

        data = []
        for table in result:
            for record in table.records:
                data.append({
                    'time': record.get_time().isoformat(),
                    'value': round(record.get_value(), 6) if record.get_value() else 0
                })

        return jsonify({
            'status': 'success',
            'measurement': measurement,
            'field': field,
            'data': data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        health = influx_client.health()
        return jsonify({
            'status': 'ok',
            'influxdb': health.status,
            'influxdb_version': health.version
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    web_config = config.get('web', {})
    app.run(
        host=web_config.get('host', '0.0.0.0'),
        port=web_config.get('port', 8060),
        debug=False
    )
