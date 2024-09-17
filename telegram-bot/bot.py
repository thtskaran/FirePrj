import os
import json
import requests
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button

# Load environment variables
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
FLASK_ENDPOINT = os.getenv('FLASK_ENDPOINT')
GEO_API_KEY = os.getenv('GEO_API_KEY')

# Initialize Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# In-memory dictionary to track user requests and state
user_requests = {}
requesting_coordinates = set()
awaiting_severity = {}

# Load user requests from JSON file
def load_user_requests():
    global user_requests
    if os.path.exists('user_requests.json'):
        with open('user_requests.json', 'r') as f:
            user_requests = json.load(f)

# Save user requests to JSON file
def save_user_requests():
    with open('user_requests.json', 'w') as f:
        json.dump(user_requests, f)

load_user_requests()

# Geocoding function
def get_coordinates(api_key, address):
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        'q': address,
        'key': api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['geometry']
        else:
            return None
    else:
        return None

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Welcome! I am here to help you. If you need assistance, use words such as: fire, case, report, emergency, accident, help.')

@client.on(events.NewMessage(incoming=True))
async def chat_handler(event):
    user_id = event.sender_id
    message = event.message.message.lower()

    # Ignore messages from the bot itself
    if user_id == (await client.get_me()).id:
        return

    if user_id in awaiting_severity:
        await event.respond('Please choose the severity on a scale of 1-10 using the provided buttons.')
    elif user_id in requesting_coordinates:
        try:
            message_parts = message.split(',')

            if len(message_parts) != 2:
                await event.respond('Invalid format. Please provide the coordinates in correct format: latitude, longitude.')
                return
            
            latitude, longitude = float(message_parts[0].strip()), float(message_parts[1].strip())
            awaiting_severity[user_id] = [latitude, longitude]
            requesting_coordinates.remove(user_id)
            
            # Ask for severity
            buttons = [
                [Button.inline(str(i), str(i)) for i in range(j, j + 5)]
                for j in range(1, 11, 5)
            ]
            await event.respond(
                'Please rate the severity of the case on a scale of 1-10:',
                buttons=buttons
            )
        except Exception as e:
            await event.respond(f'Error: {str(e)}')
    elif any(keyword in message for keyword in ['fire', 'case', 'report', 'emergency', 'accident', 'help']):
        await event.respond('We are here to help! Please provide your address (street name, city):')
        requesting_coordinates.add(user_id)
    elif user_id in user_requests:
        # If user already has a report, fetch the status of their report
        report_hash = user_requests[user_id]
        response = requests.get(f'{FLASK_ENDPOINT}/repStatus', params={'hash': report_hash})
        response_data = response.json()
        
        if 'error' in response_data:
            await event.respond(f"Error: {response_data['error']}")
        else:
            truck_assigned = response_data['truck_assigned']
            eta = response_data['ETA']
            await event.respond(f'Truck Assigned: {truck_assigned}\nETA: {eta}')
    else:
        await event.respond('Hello! How can I assist you today?')

@client.on(events.CallbackQuery)
async def callback_query_handler(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')

    if user_id in awaiting_severity:
        try:
            severity = int(data)
            coordinates = awaiting_severity[user_id]
            data = {
                'user_id': user_id,
                'coordinates': coordinates,
                'severity': severity
            }

            response = requests.post(f'{FLASK_ENDPOINT}/newReport', json=data)
            response_data = response.json()

            if 'error' in response_data:
                await event.respond(f"Error: {response_data['error']}")
            else:
                report_hash = response_data['hash']
                user_requests[user_id] = report_hash
                save_user_requests()
                await event.respond(f'Report submitted successfully with severity {severity}. Your report hash is {report_hash}')

            del awaiting_severity[user_id]
                
        except Exception as e:
            await event.respond(f'Error: {str(e)}')

@client.on(events.NewMessage(incoming=True))
async def address_handler(event):
    user_id = event.sender_id
    message = event.message.message.lower()

    # Check if we are expecting address from the user
    if user_id in requesting_coordinates:
        coordinates = get_coordinates(GEO_API_KEY, message)

        if coordinates:
            latitude = coordinates['lat']
            longitude = coordinates['lng']
            awaiting_severity[user_id] = [latitude, longitude]
            requesting_coordinates.remove(user_id)
            
            # Ask for severity
            buttons = [
                [Button.inline(str(i), str(i)) for i in range(j, j + 5)]
                for j in range(1, 11, 5)
            ]
            await event.respond(
                'We have fetched the coordinates. Please rate the severity of the case on a scale of 1-10:',
                buttons=buttons
            )
        else:
            await event.respond('Unable to fetch coordinates. Please provide the coordinates in the format: latitude, longitude.')

client.start()
client.run_until_disconnected()
