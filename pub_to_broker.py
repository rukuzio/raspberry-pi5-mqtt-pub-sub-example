import paho.mqtt.client as mqtt
import time
import psutil
import json

# MQTT Configuration
broker = "localhost"
port = 1883
topic = "raspberrypi/system_health"

# Function to get CPU temperature
def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0  # Convert from millidegree Celsius
        return temp
    except FileNotFoundError:
        return None

# Function to get system health metrics
def get_system_metrics():
    cpu_temp = get_cpu_temperature()
    cpu_usage = psutil.cpu_percent(interval=1)  # CPU usage over 1 second
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    return {
        "cpu_temperature": cpu_temp,
        "cpu_usage_percent": cpu_usage,
        "memory_used_mb": memory.used / (1024 * 1024),
        "memory_total_mb": memory.total / (1024 * 1024),
        "disk_used_percent": disk.percent,
    }

# Function to get network metrics
def get_network_metrics():
    net = psutil.net_io_counters()  # Collect network I/O statistics
    
    return {
        "network_sent_mb": net.bytes_sent / (1024 * 1024),  # Convert to MB
        "network_recv_mb": net.bytes_recv / (1024 * 1024)   # Convert to MB
    }

# Initialize MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, port)

try:
    while True:
        # Get system and network metrics
        system_metrics = get_system_metrics()
        network_metrics = get_network_metrics()

        # Combine both metrics into one dictionary
        metrics = {**system_metrics, **network_metrics}
        
        print(f"Publishing metrics: {metrics}")
        
        # Publish metrics as JSON
        client.publish(topic, json.dumps(metrics))
        
        # Wait for n minutes
        time.sleep(600)  # in seconds
except KeyboardInterrupt:
    print("Script stopped by user.")
except Exception as e:
    print(f"Error: {e}")
finally:
    client.disconnect()
