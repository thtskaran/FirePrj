from flask import Flask, request, jsonify
from collections import namedtuple
import json
import os
import uuid
from datetime import datetime, timedelta
import math

app = Flask(__name__)

# Named Tuples
Truck = namedtuple('Truck', ['license_plate', 'coordinates', 'available'])
AssignedTruck = namedtuple('AssignedTruck', ['license_plate', 'assigned_hash'])

# Hardcoded Truck Data
trucks = [
    Truck(license_plate='ABC123', coordinates=(34.052235, -118.243683), available=True),
    Truck(license_plate='XYZ789', coordinates=(34.052235, -118.243683), available=True),
]

# Log Paths
TRUCKS_LOG_PATH = './logs/trucks/'
REPORTS_LOG_PATH = './logs/reports/'

# Ensure log directories exist
os.makedirs(TRUCKS_LOG_PATH, exist_ok=True)
os.makedirs(REPORTS_LOG_PATH, exist_ok=True)

# Utility function to save data
def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# Utility function to load data
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    else:
        return {}

# Haversine formula to calculate distance between two points
def haversine(coord1, coord2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Get travel time at 45 km/h
def get_travel_time_km(distance):
    return distance / 45

@app.route('/newReport', methods=['POST'])
def new_report():
    data = request.json
    user_id = data.get('user_id')
    coordinates = tuple(data.get('coordinates'))
    severity = data.get('severity')

    if not (1 <= severity <= 10):
        return jsonify({"error": "Severity must be between 1 and 10"}), 400

    report_hash = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    report = {
        "user_id": user_id,
        "coordinates": coordinates,
        "severity": severity,
        "hash": report_hash,
        "timestamp": timestamp,
        "processed": False,
        "truck_assigned": None,
        "ETA": None
    }

    reports_data = load_json(os.path.join(REPORTS_LOG_PATH, 'incident_reports.json'))
    reports_data[report_hash] = report
    save_json(os.path.join(REPORTS_LOG_PATH, 'incident_reports.json'), reports_data)

    return jsonify({"hash": report_hash})

@app.route('/getData', methods=['GET'])
def get_data():
    reports_data = load_json(os.path.join(REPORTS_LOG_PATH, 'incident_reports.json'))
    return jsonify(reports_data)

@app.route('/repStatus', methods=['GET'])
def rep_status():
    report_hash = request.args.get('hash')
    reports_data = load_json(os.path.join(REPORTS_LOG_PATH, 'incident_reports.json'))

    report = reports_data.get(report_hash)
    if report:
        return jsonify(report)
    else:
        return jsonify({"error": "Report not found"}), 404

@app.route('/trucksManagement', methods=['GET'])
def trucks_management():
    assigned_trucks_data = load_json(os.path.join(TRUCKS_LOG_PATH, 'assigned_trucks.json'))
    return jsonify(assigned_trucks_data)

if __name__ == '__main__':
    app.run(debug=True)
