from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA=="
ORG = "ai_factory"
BUCKET = "machine_data"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=ORG
)

query_api = client.query_api()
