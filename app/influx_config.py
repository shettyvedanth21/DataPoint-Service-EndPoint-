"""
InfluxDB Configuration Module

Initializes InfluxDB client, write_api, and query_api for use across the application.
"""

from influxdb_client import InfluxDBClient

# InfluxDB Configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA=="
ORG = "ai_factory"
BUCKET = "machine_data"

# Initialize InfluxDB Client
client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)

# Initialize Write API
write_api = client.write_api()

# Initialize Query API
query_api = client.query_api()
