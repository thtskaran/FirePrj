import os
import json
import uuid
from datetime import datetime, timedelta
from typing import NamedTuple
from collections import deque
from flask import Flask, request, jsonify
from haversine import haversine
import time
from random import randint

app = Flask(__name__)

# Paths
REPORTS_LOG_PATH = './logs/reports'
TRUCKS_LOG_PATH = './logs/trucks'
INCIDENT_REPORTS_FILE = os.path.join(REPORTS_LOG_PATH, 'incident_reports.json')
TRUCKS_STATUS_FILE = os.path.join(TRUCKS_LOG_PATH, 'trucks_status.json')
TRUCKS_MANAGEMENT_FILE = os.path.join(TRUCKS_LOG_PATH, 'trucks_management.json')

# Hardcoded Truck Data
class Truck(NamedTuple):
    license_plate: str
    coordinates: tuple
    available: bool

class TruckAssignment(NamedTuple):
    license_plate: str
    assigned_hash: str

trucks = [
    Truck("ABC123", (40.712776, -74.005974), True),
    Truck("DEF456", (34.052235, -118.243683), True),
    # Add 11 more hardcoded Truck entries here
]

assignments = []

incident_queue = deque(maxlen=100)

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as file:
        return json.load(file)

def save_json(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

def log_event(message):
    timestamp = datetime.now().isoformat()
    with open(os.path.join(REPORTS_LOG_PATH, 'events.log'), 'a') as log_file:
        log_file.write(f'[{timestamp}] {message}\n')

def assign_truck(report):
    global trucks
    available_trucks = [truck for truck in trucks if truck.available]
    
    if not available_trucks:
        return None
    
    # Assign the nearest available truck
    nearest_truck = min(available_trucks, key=lambda t: haversine(t.coordinates, report['coordinates']))
    nearest_truck_index = trucks.index(nearest_truck)
    
    trucks[nearest_truck_index] = nearest_truck._replace(available=False)
    assignments.append(TruckAssignment(nearest_truck.license_plate, report['hash']))
    
    return nearest_truck.license_plate

@app.route('/newReport', methods=['POST'])
def new_report():
    data = request.get_json()
    
    # Extract Parameters
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
    
    incident_queue.append((severity, report))

    log_event("New report arrived")
    
    # Save report immediately
    incident_reports = load_json(INCIDENT_REPORTS_FILE)
    incident_reports[report_hash] = report
    save_json(INCIDENT_REPORTS_FILE, incident_reports)

    return jsonify({"hash": report_hash})

@app.route('/getData', methods=['GET'])
def get_data():
    incident_reports = load_json(INCIDENT_REPORTS_FILE)
    return jsonify(incident_reports)

@app.route('/repStatus', methods=['GET'])
def rep_status():
    report_hash = request.args.get('hash')

    incident_reports = load_json(INCIDENT_REPORTS_FILE)
    report = incident_reports.get(report_hash)

    if not report:
        return jsonify({"error": "Report not found"}), 404

    return jsonify({
        "truck_assigned": report["truck_assigned"],
        "ETA": report["ETA"]
    })

@app.route('/trucksManagement', methods=['GET'])
def trucks_management():
    trucks_management_data = [
        {"license_plate": assignment.license_plate, "assigned_hash": assignment.assigned_hash}
        for assignment in assignments
    ]
    save_json(TRUCKS_MANAGEMENT_FILE, trucks_management_data)
    return jsonify(trucks_management_data)

@app.route('/killSwitch', methods=['POST'])
def kill_switch():
    data = request.get_json()
    password = data.get('password')

    if password != "1234":
        return jsonify({"error": "Unauthorized"}), 401

    # Delete all log files
    for log_file in [INCIDENT_REPORTS_FILE, TRUCKS_STATUS_FILE, TRUCKS_MANAGEMENT_FILE]:
        if os.path.exists(log_file):
            os.remove(log_file)

    # Clear in-memory data structures
    global trucks, assignments, incident_queue
    trucks = [
        Truck("ABC123", (40.712776, -74.005974), True),
        Truck("DEF456", (34.052235, -118.243683), True),
        # Add 11 more hardcoded Truck entries here
    ]
    assignments.clear()
    incident_queue.clear()

    log_event("Kill switch activated: All logs deleted and memory cleared")

    return jsonify({"message": "All logs deleted and memory cleared"})

# Background Task to Dispatch Trucks
@app.before_first_request
def start_dispatcher():
    def dispatcher():
        while True:
            if incident_queue:
                _, report = max(incident_queue, key=lambda x: x[0])
                incident_queue.remove((report['severity'], report))
                
                assigned_truck = assign_truck(report)
                if assigned_truck:
                    log_event(f"New truck assigned: {assigned_truck}")
                    report['truck_assigned'] = assigned_truck
                    
                    # Wait for 120 seconds to gather more reports
                    time.sleep(120)
                    
                    # Compute ETA and update status
                    travel_time = haversine(report['coordinates'], trucks[0].coordinates) / 45 * 60
                    random_dispatch_time = randint(1, 3) * 60
                    ETA = datetime.now() + timedelta(minutes=(travel_time + 3))
                    
                    report['ETA'] = ETA.isoformat()
                    report['processed'] = True
                    
                    # Log ETA assignment
                    minutes_left = int((ETA - datetime.now()).total_seconds() // 60)
                    formatted_eta = ETA.strftime("%d/%m/%Y %H:%M:%S")
                    log_event(f"ETA assigned: {formatted_eta}, Minutes left: {minutes_left}")
                    
                    incident_reports = load_json(INCIDENT_REPORTS_FILE)
                    incident_reports[report['hash']] = report
                    save_json(INCIDENT_REPORTS_FILE, incident_reports)
                    
                    # Debugging log to ensure the report is saved correctly
                    log_event(f"Report updated in file: {incident_reports[report['hash']]}")
                else:
                    log_event("No available trucks to assign")
            else:
                log_event("Incident queue is empty")
            
            time.sleep(1)
    
    import threading
    dispatch_thread = threading.Thread(target=dispatcher)
    dispatch_thread.daemon = True
    dispatch_thread.start()

if __name__ == '__main__':
    os.makedirs(REPORTS_LOG_PATH, exist_ok=True)
    os.makedirs(TRUCKS_LOG_PATH, exist_ok=True)
    
    save_json(TRUCKS_STATUS_FILE, [t._asdict() for t in trucks])
    
    app.run(debug=True)