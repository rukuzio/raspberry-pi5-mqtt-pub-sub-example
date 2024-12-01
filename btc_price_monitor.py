import os
from dotenv import load_dotenv
import websocket
import threading
import time
import json
import requests

# Load environment variables
load_dotenv()
auth = os.getenv("BEARER")

# WebSocket and Webhook configurations
websocket_url = "wss://push.coinmarketcap.com/ws?device=web&client_source=home_page"
webhook_url = "https://fastwebhooks.com/mqtt"
crypto_ids = "1"  # ID of the cryptocurrency to monitor (e.g., Bitcoin)

headers = {
    "Authorization": auth,
    "Content-Type": "application/json",
}

# Shared variable for the latest response
latest_data = None

# WebSocket event handlers
def on_message(ws, message):
    global latest_data
    try:
        data = json.loads(message)

        # Filter for data with `id: 1`
        if "d" in data and data["d"].get("id") == 1:
            # Safely extract keys with defaults for missing values
            latest_data = {
                "id": data["d"].get("id"),
                "price": data["d"].get("p", None),  # Price
                "price_change_24h": data["d"].get("p24h", None),  # 24h price change
                "market_cap": data["d"].get("mc", None),  # Market cap
                "as": data["d"].get("as", None),  # Available supply
                "timestamp": data.get("t"),  # Timestamp
            }
            print(f"Updated Bitcoin data: {latest_data}")
    except Exception as e:
        print(f"Error processing WebSocket message: {e}")


def on_open(ws):
    print("WebSocket connection opened")

    # Construct subscription messages
    subscription_15s = {
        "method": "RSUBSCRIPTION",
        "params": [f"main-site@crypto_price_15s@{{}}@normal", crypto_ids],
    }

    subscription_5s = {
        "method": "RSUBSCRIPTION",
        "params": [f"main-site@crypto_price_5s@{{}}@normal", crypto_ids],
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


# Function to send the latest data to the webhook every 15 seconds
def send_to_webhook():
    while True:
        if latest_data:
            try:
                response = requests.post(webhook_url, headers=headers, json=latest_data)
                print(f"Webhook response: {response.status_code}, {response.text}")
            except Exception as e:
                print(f"Error sending to webhook: {e}")
        else:
            print("No data available to send to webhook yet.")
        
        time.sleep(15)


# Main function to start WebSocket and webhook threads
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

    # Start the webhook sender thread
    webhook_thread = threading.Thread(target=send_to_webhook)
    webhook_thread.daemon = True
    webhook_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")


if __name__ == "__main__":
    main()
