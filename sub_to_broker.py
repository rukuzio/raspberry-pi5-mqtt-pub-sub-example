import os
import paho.mqtt.client as mqtt
import requests
import json
from dotenv import load_dotenv
import warnings

# Suppress Deprecation Warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables
load_dotenv()
auth = os.getenv("BEARER")

# MQTT configuration
broker = "localhost"
port = 1883
topic = "raspberrypi/system_health"

# Webhook URL
webhook_url = "https://fastwebhooks.com/mqtt"
headers = {"Authorization": auth}

# Define callback functions
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(topic)
    else:
        print(f"Failed to connect, return code {rc}")

def handle_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker")
    if rc != 0:
        print("Unexpected disconnection. Reconnecting...")
        client.reconnect()

def handle_message(client, userdata, message):
    raw_payload = message.payload.decode()
    print(f"Message received: {raw_payload}")

    try:
        payload = json.loads(raw_payload)
        print(f"Parsed payload: {payload}")
        response = requests.post(webhook_url, headers=headers, json=payload)
        print(f"Webhook response: {response.status_code}, {response.text}")
    except json.JSONDecodeError:
        print(f"Invalid JSON payload: {raw_payload}")
    except Exception as e:
        print(f"Error forwarding to webhook: {e}")

# Initialize MQTT client
client = mqtt.Client()
client.on_connect = handle_connect
client.on_disconnect = handle_disconnect
client.on_message = handle_message

# Connect and start the loop
try:
    client.connect(broker, port)
    client.loop_forever()
except KeyboardInterrupt:
    print("Stopping MQTT client...")
    client.disconnect()
except Exception as e:
    print(f"Error: {e}")
