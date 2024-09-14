# Incident Report and Truck Assignment System

### Overview
This Flask application is designed to handle incident reports and automatically assign trucks based on the severity and location of incidents. The system includes multiple endpoints for creating reports, checking report statuses, managing truck assignments, and a kill switch to reset all data.

## Table of Contents
- [Requirements](#requirements)
- [Setup Instructions](#setup-instructions)
- [Project Structure](#project-structure)
- [Endpoints](#endpoints)
  - [/newReport](#newreport)
  - [/getData](#getdata)
  - [/repStatus](#repstatus)
  - [/trucksManagement](#trucksmanagement)
  - [/killSwitch](#killswitch)
- [Edge Cases and CURL Requests](#edge-cases-and-curl-requests)

## Requirements
- Python 3.x
- Flask
- Haversine
- uuid
- requests

## Setup Instructions
1. **Clone the Repository:**
   ```sh
   git clone https://github.com/your_username/incident-truck-assignment.git
   cd incident-truck-assignment
   ```

2. **Create a Virtual Environment (optional but recommended):**
   ```sh
   python -m venv env
   source env/bin/activate    # On Windows use `env\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```sh
   python app.py
   ```

## Project Structure
```
.
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
└── logs/                   # Directory for storing log files
    ├── reports/
    │   ├── incident_reports.json 
    │   └── events.log
    └── trucks/
        ├── trucks_status.json
        └── trucks_management.json
```

## Endpoints
### /newReport
**Method:** POST

Creates a new incident report.

**Payload:**
```json
{
    "user_id": "user123",
    "coordinates": [40.712776, -74.005974],
    "severity": 5
}
```

**Response:**
```json
{
    "hash": "unique_report_hash"
}
```

**CURL:**
```sh
curl -X POST http://127.0.0.1:5000/newReport -H "Content-Type: application/json" -d '{"user_id":"user123", "coordinates":[40.712776, -74.005974], "severity":5}'
```

### /getData
**Method:** GET

Retrieves all incident reports.

**Response:**
```json
{
    "report_hash_1": {...},
    "report_hash_2": {...}
}
```

**CURL:**
```sh
curl -X GET http://127.0.0.1:5000/getData
```

### /repStatus
**Method:** GET

Checks the status of a specific report.

**Query Parameters:**
- `hash`: Unique hash of the report.

**Response:**
```json
{
    "truck_assigned": "ABC123",
    "ETA": "14/09/2024 13:12:56"
}
```

**CURL:**
```sh
curl -X GET "http://127.0.0.1:5000/repStatus?hash=unique_report_hash"
```

### /trucksManagement
**Method:** GET

Provides details on current truck assignments.

**Response:**
```json
[
    {
        "license_plate": "ABC123",
        "assigned_hash": "unique_report_hash"
    },
    ...
]
```

**CURL:**
```sh
curl -X GET http://127.0.0.1:5000/trucksManagement
```

### /killSwitch
**Method:** POST

Deletes all logs and resets in-memory data structures.

**Payload:**
```json
{
    "password": "1234"
}
```

**Response:**
```json
{
    "message": "All logs deleted and memory cleared"
}
```

**CURL:**
```sh
curl -X POST http://127.0.0.1:5000/killSwitch -H "Content-Type: application/json" -d '{"password":"1234"}'
```

## Edge Cases and CURL Requests

### Invalid Severity in /newReport
**Description:** Severity value must be between 1 and 10.

**CURL:**
```sh
curl -X POST http://127.0.0.1:5000/newReport -H "Content-Type: application/json" -d '{"user_id":"user123", "coordinates":[40.712776, -74.005974], "severity":11}'
```

**Response:**
```json
{
    "error": "Severity must be between 1 and 10"
}
```

### Unauthorized Access to /killSwitch
**Description:** Attempting to access the kill switch with an incorrect password.

**CURL:**
```sh
curl -X POST http://127.0.0.1:5000/killSwitch -H "Content-Type: application/json" -d '{"password":"wrong_password"}'
```

**Response:**
```json
{
    "error": "Unauthorized"
}
```

### Non-existent Report in /repStatus
**Description:** Checking the status of a report that does not exist.

**CURL:**
```sh
curl -X GET "http://127.0.0.1:5000/repStatus?hash=non_existent_hash"
```

**Response:**
```json
{
    "error": "Report not found"
}
```