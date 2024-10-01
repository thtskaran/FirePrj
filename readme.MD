# Project Overview

This project was created for an internal hackathon for Smart India Hackathon (SIH). The goal is to develop a system for managing incident reports and truck assignments. Although initially developed for the hackathon, there are plans to make it a real-world tool.

## Features

### Incident Reporting

Users can report incidents with details such as user ID, coordinates, and severity.

**Endpoint:** `/newReport`

**Method:** POST

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

### Report Status

Check the status of a report using its unique hash.

**Endpoint:** `/repStatus`

**Method:** GET

**Parameters:**
- `hash`: The unique hash of the report.

**Response:**
```json
{
    "truck_assigned": "ABC123",
    "ETA": "14/09/2024 17:51:43"
}
```

**CURL:**
```sh
curl -X GET "http://127.0.0.1:5000/repStatus?hash=unique_report_hash"
```

### Truck Management

Provides details on current truck assignments.

**Endpoint:** `/trucksManagement`

**Method:** GET

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

### Kill Switch

Deletes all logs and resets in-memory data structures.

**Endpoint:** `/killSwitch`

**Method:** POST

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

## Technologies Used

### Flask

Flask is used to create the API endpoints for incident reporting, status checking, and truck management.

### Haversine

The Haversine formula is used to calculate the distance between two points on the Earth's surface, which helps in determining the nearest available truck to an incident location.

### Reverse Geocoding

Reverse geocoding is used to convert coordinates into a human-readable address, which can be useful for logging and reporting purposes.

### Random Delay in Truck Dispatch

Currently, a random delay is used to simulate the time it takes for a truck to be dispatched to an incident. In future production versions, this will be replaced with a more realistic model based on traffic data, distance, and other factors.

## Truck Dispatch Logic

When an incident is reported, the system assigns the nearest available truck to the incident based on the Haversine distance. The truck's estimated time of arrival (ETA) is calculated and returned in the response. The random delay in truck dispatch will be changed in future production to something more realistic.

## Telegram Bot

The project includes a Telegram bot for user interaction.

### Start Command

**Description:** Starts the bot and provides a welcome message.

### Message Handler

**Description:** Handles incoming messages and processes user requests.

### Callback Query Handler

**Description:** Handles callback queries from inline buttons.

### User Requests

User requests are tracked in-memory and saved to a JSON file.

**Load User Requests:**
```py
def load_user_requests():
    global user_requests
    if os.path.exists('user_requests.json'):
        with open('user_requests.json', 'r') as f:
            user_requests = json.load(f)
```

**Save User Requests:**
```py
def save_user_requests():
    with open('user_requests.json', 'w') as f:
        json.dump(user_requests, f)
```

## Logging

Events are logged to a file for auditing and debugging purposes.

**Log Event:**
```py
def log_event(message):
    timestamp = format_timestamp(datetime.now())
    with open(os.path.join(REPORTS_LOG_PATH, 'events.log'), 'a') as log_file:
        log_file.write(f'[{timestamp}] {message}\n')
```

## Requirements

The project dependencies are listed in [`requirements.txt`](command:_github.copilot.openRelativePath?%5B%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2FUsers%2Fkaran%2FDocuments%2FProjects%2FFirePrj%2Frequirements.txt%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%223fbfc87f-7457-481f-8d1f-66f7d38bee94%22%5D "/Users/karan/Documents/Projects/FirePrj/requirements.txt"):

```txt
Flask==2.2.5
werkzeug==3.0.4
haversine==2.5.1
uuid==1.30
requests==2.27.1
python-dotenv==0.19.2
flask_cors
```