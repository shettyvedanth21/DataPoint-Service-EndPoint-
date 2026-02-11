import paho.mqtt.client as mqtt
import json
import time
import random

client = mqtt.Client()
client.connect("localhost", 1883, 60)

while True:
    data = {
        "voltage": random.uniform(220, 240),
        "current": random.uniform(0.5, 2.0),
        "power": random.uniform(100, 500),
        "energy": random.uniform(0.01, 0.2)
    }

    client.publish("factory/air_compressor/metrics", json.dumps(data))
    print("Published:", data)
    time.sleep(5)
