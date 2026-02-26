import json
import logging
import os
import paho.mqtt.client as mqtt
from pathlib import Path
from dotenv import load_dotenv
from influxdb_client import Point, WritePrecision
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "factory/air_compressor/metrics")

# InfluxDB Configuration
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA==")
ORG = os.getenv("INFLUX_ORG", "ai_factory")
BUCKET = os.getenv("INFLUX_BUCKET", "machine_data")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_write_api():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
    return client.write_api()

def on_connect(client, userdata, flags, rc):
    """Called when connected to MQTT broker"""
    if rc == 0:
        logger.info(f"Connected to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect, return code: {rc}")

def on_message(client, userdata, msg):
    """Called when message received on subscribed topic"""
    try:
        # Parse JSON payload
        data = json.loads(msg.payload.decode())
        
        # Get current timestamp
        timestamp = datetime.now(timezone.utc)
        
        # Get write API
        write_api = get_write_api()
        
        # Create dynamic points for each metric in the data
        points = []
        for property_id, value in data.items():
            point = (
                Point("sensor_data")
                .tag("device_id", "mqtt_device")  # Default device for MQTT data
                .tag("property_id", property_id)
                .field(property_id, float(value))
                .time(timestamp, WritePrecision.NS)
            )
            points.append(point)
        # Write all points to InfluxDB
        write_api.write(bucket=BUCKET, org=ORG, record=points)
        logger.info(f"Stored from MQTT: {data}")    
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def main():
    """Start MQTT service"""
    # Create MQTT client
    client_mqtt = mqtt.Client()
    
    # Set callback functions
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message
    
    # Connect and start listening
    logger.info(f"Starting MQTT service...")
    logger.info(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    
    client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Keep the connection running
    client_mqtt.loop_forever()

if __name__ == "__main__":
    main()
