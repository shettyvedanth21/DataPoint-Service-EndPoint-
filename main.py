from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision

app = FastAPI()

url = "http://localhost:8086"
token = "YOUR_TOKEN"
org = "ai_factory"
bucket = "machine_data"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

class SensorData(BaseModel):
    device_id: str
    property_id: str
    value: float
    timestamp: datetime | None = None

@app.post("/ingest")
def ingest_data(data: SensorData):
    timestamp = data.timestamp or datetime.now(timezone.utc)

    point = (
        Point("air_compressor")
        .tag("device_id", data.device_id)
        .tag("property_id", data.property_id)
        .field("value", data.value)
        .time(timestamp, WritePrecision.NS)
    )

    write_api.write(bucket=bucket, org=org, record=point)

    return {"status": "ok"}
