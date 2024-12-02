from datetime import datetime, timezone
import os
import time
from dotenv import load_dotenv
import websocket
import threading
import json
import requests

# Load environment variables
load_dotenv()
auth = os.getenv("X5_BEARER")
post_url = os.getenv("POST_URL")

# WebSocket and Webhook configurations
websocket_url = "wss://push.coinmarketcap.com/ws?device=web&client_source=home_page"
crypto_ids = [1, 1027, 2010, 5426, 29210, 29587, 7653]

headers = {
    "Cookie": auth,
    "Content-Type": "application/json",
}
print(post_url)

# Function to convert Unix timestamp to ISO datetime
def convert_to_iso(unix_timestamp):
    try:
        # Convert the Unix timestamp to milliseconds if needed
        if len(str(unix_timestamp)) > 10:
            unix_timestamp = int(unix_timestamp) / 1000.0

        # Convert to ISO 8601 datetime with UTC timezone
        return datetime.fromtimestamp(unix_timestamp, timezone.utc).isoformat()
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return None


# WebSocket event handlers
def on_message(ws, message):
    try:
        data = json.loads(message)

        # Ensure data contains a "d" field and process each cryptocurrency
        if "d" in data:
            crypto_id = data["d"].get("id")
            if crypto_id in crypto_ids:  # Dynamically check if ID is in the list
                iso_timestamp = convert_to_iso(data.get("t"))

                latest_data = {"properties": {
                    "c_cmccryptoid": crypto_id,
                    "c_price": data["d"].get("p", None),  # Price
                    "c_twentyfourhourpricechange": data["d"].get("p24h", None),  # 24h price change
                    "c_marketcap": data["d"].get("mc", None),  # Market cap
                    "c_circulatingsupply": data["d"].get("as", None),  # Available supply
                    "c_timestampu": iso_timestamp,  # Original timestamp
                }}
                print(f"Updated data for ID {crypto_id}: {latest_data}")

                # Send to webhook
                try:
                    response = requests.post(post_url, headers=headers, json=latest_data)
                    print(f"Emaint response: {response.status_code}, {response.text}")
                except Exception as e:
                    print(f"Error sending to Emaint: {e}")
    except Exception as e:
        print(f"Error processing WebSocket message: {e}")


def on_open(ws):
    print("WebSocket connection opened")

    # Construct subscription messages
    subscription_15s = {
        "method": "RSUBSCRIPTION",
        "params": [f"main-site@crypto_price_15s@{{}}@normal", ",".join(map(str, crypto_ids))],
    }

    subscription_5s = {
        "method": "RSUBSCRIPTION",
        "params": [f"main-site@crypto_price_5s@{{}}@normal", ",".join(map(str, crypto_ids))],
    }

    # Send subscription messages
    ws.send(json.dumps(subscription_15s))
    print(f"Sent subscription message: {subscription_15s}")

    ws.send(json.dumps(subscription_5s))
    print(f"Sent subscription message: {subscription_5s}")


def on_error(ws, error):
    print(f"WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")


# Main function to start WebSocket connection
def main():
    # Add WebSocket headers to mimic a browser
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        websocket_url,
        header={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Sec-Fetch-Mode": "cors",
            "Sec-WebSocket-Protocol": "json",
        },
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close,
    )

    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")


if __name__ == "__main__":
    main()
