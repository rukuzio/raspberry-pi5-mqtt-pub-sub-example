import os
import paho.mqtt.client as mqtt
import requests
import json
from dotenv import load_dotenv

load_dotenv()
auth = os.getenv("BEARER")

# MQTT configuration
broker = "localhost"
port = 1883
topic = "raspberrypi/system_health"


# Webhook URL
webhook_url = "https://fastwebhooks.com/mqtt"

headers = {
"Authorization": auth
}


def on_message(client, userdata, message):
    raw_payload = message.payload.decode()  # Decode the raw message
    print(f"Message received: {raw_payload}")

    try:
        # If payload is not JSON, convert it
        if raw_payload.startswith("{") and raw_payload.endswith("}"):
            # Attempt to parse as JSON
            print(f"Raw MQTT payload: {message.payload}")
            payload = json.loads(raw_payload.replace("'", "\""))  # Convert single to double quotes if necessary
        else:
            print("Payload is not JSON-formatted.")
            return

        # Forward the message to the webhook
        response = requests.post(webhook_url, headers=headers, json=payload)
        print(f"Webhook response: {response.status_code}, {response.text}")

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"Raw MQTT payload: {message.payload}")
        print(f"Error forwarding to webhook: {e}")

# Initialize the MQTT client
client = mqtt.Client()
client.on_message = on_message

# Connect and subscribe
try:
    client.connect(broker, port)
    client.subscribe(topic)
    print(f"Subscribed to topic {topic}")
    client.loop_forever()  # Block and listen for messages
except Exception as e:
    print(f"Error: {e}")
