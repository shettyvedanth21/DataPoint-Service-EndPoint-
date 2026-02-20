from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
from influxdb_client import Point, WritePrecision
from app.influx_config import write_api, ORG, BUCKET   
app = FastAPI()
class SensorData(BaseModel):
    device_id: str
    property_id: str   # example: temperature / voltage / current
    value: float
    timestamp: datetime | None = None
@app.post("/ingest")
def ingest_data(data: SensorData):
    timestamp = data.timestamp or datetime.now(timezone.utc)

    point = (
        Point("sensor_data")             
        .tag("device_id", data.device_id)
        .tag("property_id", data.property_id)
        .field(data.property_id, data.value) 
        .time(timestamp, WritePrecision.NS)
    )

    write_api.write(bucket=BUCKET, org=ORG, record=point)
    return {"status": "ok"}
