import paho.mqtt.client as mqtt
import json
import time
import random
import sys
import argparse

def generate_value():
    """Generate random value"""
    return round(random.uniform(0, 100), 2)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MQTT Sensor Data Publisher")
    parser.add_argument("--properties", "-p", nargs="+", 
                        help="Property IDs to publish (e.g., voltage temperature pressure)")
    parser.add_argument("--device-id", "-d",
                        help="Device ID (required)")
    parser.add_argument("--broker", default="localhost",
                        help="MQTT Broker address")
    parser.add_argument("--port", type=int, default=1883,
                        help="MQTT Broker port")
    parser.add_argument("--topic", "-t",
                        help="MQTT Topic")
    parser.add_argument("--interval", type=int, default=5,
                        help="Publish interval in seconds")
    args = parser.parse_args()

    # Both device_id, properties, and topic are required
    if not args.properties or not args.device_id or not args.topic:
        print("Error: Please specify -d, -p, and -t flags")
        print("Example: python publisher.py -d D01 -p voltage -t factory/sensors/data")
        sys.exit(1)   
    properties = args.properties
    
    print(f"Publishing for device: {args.device_id}")
    print(f"Properties: {properties}")
    print(f"Broker: {args.broker}:{args.port}")
    print(f"Topic: {args.topic}")
    print(f"Interval: {args.interval} seconds")
    print("-" * 40)
    
    # Create MQTT client
    client = mqtt.Client()
    client.connect(args.broker, args.port, 60)
    
    # Infinite loop to publish data
    while True:
        # Generate random data for each property
        data = {
            "device_id": args.device_id,
            "timestamp": time.time()
        }
        
        # Add each property with random value
        for prop in properties:
            data[prop] = generate_value()
        
        # Publish to MQTT topic
        client.publish(args.topic, json.dumps(data))
        print(f"Published: {data}")
        
        # Wait before next publish
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
