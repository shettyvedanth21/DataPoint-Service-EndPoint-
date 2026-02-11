import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from datetime import datetime

# InfluxDB config
INFLUX_URL = "http://localhost:8086"
TOKEN = "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA== "
ORG = "ai_factory"
BUCKET = "machine_data"

client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
write_api = client.write_api()

# MQTT config
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "bulb/sensor"


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        energy = data["energy"]
        power = data["power"]
        voltage = data["voltage"]

        point = (
            Point("bulb")
            .field("energy", energy)
            .field("power", power)
            .field("voltage", voltage)
            .time(datetime.utcnow(), WritePrecision.NS)
        )

        write_api.write(bucket=BUCKET, org=ORG, record=point)

        print("Stored:", data)

    except Exception as e:
        print("Error:", e)


client_mqtt = mqtt.Client()
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message

client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
client_mqtt.loop_forever()
