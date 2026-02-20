from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
# import analytics router
from app.routers.analytics import router as analytics_router
# import datapoint router
from app.routers.datapoint_router import router as datapoint_router
# Import InfluxDB config
from app.influx_config import client, write_api, ORG, BUCKET

app = FastAPI()
class SensorData(BaseModel):
    device_id: str
    property_id: str
    value: float
    timestamp: datetime | None = None

@app.post("/ingest")
def ingest_data(data: SensorData):
    timestamp = data.timestamp or datetime.now(timezone.utc)

    point = (
        Point("sensor_data")
        .tag("device_id", data.device_id)
        .tag("property_id", data.property_id)
        .field("value", data.value)
        .time(timestamp, WritePrecision.NS)
    )
    write_api.write(bucket=BUCKET, org=ORG, record=point)
    return {"status": "ok"}

app.include_router(analytics_router)
app.include_router(datapoint_router)
@app.post("/sensor-data")
def sensor_data(
    device_id: str = Query(..., description="Device identifier"),
    current: float = Query(..., description="Current reading"),
    voltage: float = Query(..., description="Voltage reading"),
    temperature: float = Query(..., description="Temperature reading")
):
   
    timestamp = datetime.now(timezone.utc)
    
    # Write three points: current, voltage, temperature
    points = [
        Point("sensor_data")
        .tag("device_id", device_id)
        .tag("property_id", "current")
        .field("current", current)
        .time(timestamp, WritePrecision.NS),
        Point("sensor_data")
        .tag("device_id", device_id)
        .tag("property_id", "voltage")
        .field("voltage", voltage)
        .time(timestamp, WritePrecision.NS),
        Point("sensor_data")
        .tag("device_id", device_id)
        .tag("property_id", "temperature")
        .field("temperature", temperature)
        .time(timestamp, WritePrecision.NS)
    ]
    write_api.write(bucket=BUCKET, org=ORG, record=points)
    write_api.flush()
    
    return {
        "message": "Sensor data stored successfully",
        "device_id": device_id,
        "current": current,
        "voltage": voltage,
        "temperature": temperature
    }
