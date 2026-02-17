from influxdb_client import InfluxDBClient

url = "http://localhost:8086"
token = "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA=="
org = "ai_factory"
bucket = "sensor_bucket"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()
query_api = client.query_api()
