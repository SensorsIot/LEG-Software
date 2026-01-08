from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)
TARIFFS_FILE = os.path.join(os.path.dirname(__file__), 'tariffs.json')

DEFAULT_TARIFFS = {
    'p_pv': 20.0,           # PV Delivery: house sells to community (ct/kWh)
    'p_grid_del': 6.0,      # Grid Delivery: community sells to grid (ct/kWh)
    'p_grid_con': 30.0,     # Grid Consumption: community buys from grid (ct/kWh)
}

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
    # House tariff is between PV delivery and grid consumption
    # Formula: average of p_pv and p_grid_con with small margin
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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8060, debug=False)
