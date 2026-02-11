from fastapi import FastAPI
from influxdb_client import InfluxDBClient

app = FastAPI()

# InfluxDB config
url = "http://localhost:8086"
token = "YOUR_TOKEN"
org = "YOUR_ORG"
bucket = "machine_data"

client = InfluxDBClient(url=url, token=token, org=org)
query_api = client.query_api()


@app.get("/")
def root():
    return {"message": "Machine Analytics API running"}


@app.get("/temperature")
def get_temperature():
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "air_compressor")
      |> filter(fn: (r) => r["_field"] == "temperature")
    '''
    tables = query_api.query(query)

    result = []
    for table in tables:
        for record in table.records:
            result.append({
                "time": record.get_time(),
                "temperature": record.get_value()
            })

    return result


@app.get("/pressure")
def get_pressure():
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "air_compressor")
      |> filter(fn: (r) => r["_field"] == "pressure")
    '''
    tables = query_api.query(query)

    result = []
    for table in tables:
        for record in table.records:
            result.append({
                "time": record.get_time(),
                "pressure": record.get_value()
            })

    return result
