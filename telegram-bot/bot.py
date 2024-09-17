import os
import json
import random
import requests
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerUser

# Load environment variables
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
FLASK_ENDPOINT = os.getenv('FLASK_ENDPOINT')

# Initialize Telegram client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# In-memory dictionary to track user requests and state
user_requests = {}
requesting_coordinates = set()

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
    
    if user_id in user_requests:
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
    elif user_id in requesting_coordinates:
        try:
            message_parts = message.split(',')

            if len(message_parts) != 2:
                await event.respond('Invalid format. Please provide the coordinates in correct format: latitude, longitude.')
                return
            
            latitude, longitude = float(message_parts[0].strip()), float(message_parts[1].strip())
            severity = random.randint(1, 5)
            data = {
                'user_id': user_id,
                'coordinates': [latitude, longitude],
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

            requesting_coordinates.remove(user_id)
            
        except Exception as e:
            await event.respond(f'Error: {str(e)}')
    elif any(keyword in message for keyword in ['fire', 'case', 'report', 'emergency', 'accident', 'help']):
        await event.respond('We are here to help! Please provide the coordinates in the format: latitude, longitude.')
        requesting_coordinates.add(user_id)
    else:
        await event.respond('Hello! How can I assist you today?')

async def notify_user(user_id, message):
    try:
        user = await client.get_input_entity(InputPeerUser(user_id, 0))
        await client.send_message(user, message)
    except Exception as e:
        print(f'Error notifying user {user_id}: {str(e)}')

async def check_assignments():
    while True:
        for user_id, report_hash in user_requests.items():
            response = requests.get(f'{FLASK_ENDPOINT}/repStatus', params={'hash': report_hash})
            response_data = response.json()
            if response_data.get('truck_assigned') and not response_data.get('processed'):
                message = f'Truck Assigned: {response_data["truck_assigned"]}\nETA: {response_data["ETA"]}'
                await notify_user(user_id, message)
                response_data['processed'] = True
                requests.post(f'{FLASK_ENDPOINT}/updateReport', json=response_data)
        await asyncio.sleep(60)

client.loop.create_task(check_assignments())
client.start()
client.run_until_disconnected()