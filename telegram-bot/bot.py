import os
import json
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

# In-memory dictionary to track user requests
user_requests = {}

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
    await event.respond('Welcome! Please provide your report data in the format: /report <latitude> <longitude> <severity>')

@client.on(events.NewMessage(pattern='/report'))
async def report(event):
    try:
        user_id = event.sender_id
        message = event.message.message.split()
        if len(message) != 4:
            await event.respond('Invalid format. Use: /report <latitude> <longitude> <severity>')
            return

        latitude, longitude, severity = float(message[1]), float(message[2]), int(message[3])
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
            await event.respond(f'Report submitted successfully. Your report hash is {report_hash}')
    except Exception as e:
        await event.respond(f'Error: {str(e)}')

@client.on(events.NewMessage(pattern='/track'))
async def track(event):
    try:
        user_id = event.sender_id
        if user_id not in user_requests:
            await event.respond('No report found for your user ID.')
            return

        report_hash = user_requests[user_id]
        response = requests.get(f'{FLASK_ENDPOINT}/repStatus', params={'hash': report_hash})
        response_data = response.json()

        if 'error' in response_data:
            await event.respond(f"Error: {response_data['error']}")
        else:
            truck_assigned = response_data['truck_assigned']
            eta = response_data['ETA']
            await event.respond(f'Truck Assigned: {truck_assigned}\nETA: {eta}')
    except Exception as e:
        await event.respond(f'Error: {str(e)}')

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