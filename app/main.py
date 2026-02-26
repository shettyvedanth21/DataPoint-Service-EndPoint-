
import logging
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from influxdb_client import Point, WritePrecision, InfluxDBClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================

# InfluxDB Configuration (from environment variables)
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA==")
ORG = os.getenv("INFLUX_ORG", "ai_factory")
BUCKET = os.getenv("INFLUX_BUCKET", "machine_data")

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "factory/air_compressor/metrics")


def get_influx_client():
    return InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)


def get_write_api():
    return get_influx_client().write_api()


def get_query_api():
    return get_influx_client().query_api()


# Create FastAPI app
app = FastAPI(title="Data Point Service", description="IoT Sensor Data API")

# ==================== MODELS ====================

class SensorData(BaseModel):
    """Simple sensor data model"""
    device_id: str
    property_id: str
    value: float
    timestamp: datetime | None = None


class DataPointInput(BaseModel):
    """Full datapoint input model with metadata"""
    device_id: str = Field(..., min_length=1)
    property_id: str = Field(..., min_length=1)
    value: float 
    building: str | None = None
    location: str | None = None
    status: str | None = None
   
    @field_validator('device_id', 'property_id')
    @classmethod
    def not_empty(cls, v):
        return v.strip()

class DataPointResponse(BaseModel):
    """Response model for datapoint"""
    status: str
    device_id: str
    property_id: str
    value: float


# ==================== ENDPOINTS ====================

# 1. Simple ingest endpoint
@app.post("/ingest")
def ingest_data(data: SensorData):
    """Simple sensor data ingestion"""
    timestamp = data.timestamp or datetime.now(timezone.utc)
    
    point = (
        Point("sensor_data")
        .tag("device_id", data.device_id)
        .tag("property_id", data.property_id)
        .field("value", data.value)
        .time(timestamp, WritePrecision.NS)
    )
    
    get_write_api().write(bucket=BUCKET, org=ORG, record=point)
    return {"status": "ok"}


# 2. Multi-metric sensor data endpoint (dynamic)
@app.post("/sensor-data")
def sensor_data(
    device_id: str = Query(..., description="Device identifier"),
    property_id: str = Query(..., description="Property name"),
    value: float = Query(..., description="Numeric value")
):
    """Ingest single sensor metric"""
    timestamp = datetime.now(timezone.utc)
    
    point = (
        Point("sensor_data")
        .tag("device_id", device_id)
        .tag("property_id", property_id)
        .field(property_id, float(value))
        .time(timestamp, WritePrecision.NS)
    )
    
    get_write_api().write(bucket=BUCKET, org=ORG, record=point)
    
    return {
        "message": "Sensor data stored successfully",
        "device_id": device_id,
        "property_id": property_id,
        "value": value
    }


# 3. Analytics datapoint with full metadata
@app.post("/datapoint", response_model=DataPointResponse)
def write_datapoint(data: DataPointInput):
    """Write sensor datapoint with full metadata"""
    try:
        point = (
            Point("sensor_data")
            .tag("device_id", data.device_id)
            .tag("property_id", data.property_id)
            .field("value", float(data.value))
            .time(datetime.now(timezone.utc), WritePrecision.NS)
        )
        
        # Add optional tag fields (metadata)
        if data.building:
            point = point.tag("building", data.building)
        if data.location:
            point = point.tag("location", data.location)
        if data.status:
            point = point.tag("status", data.status)
        
        get_write_api().write(bucket=BUCKET, org=ORG, record=point)
        
        return DataPointResponse(
            status="success",
            device_id=data.device_id,
            property_id=data.property_id,
            value=data.value
        )
    
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="Failed to write datapoint")


# 4. Get all data with optional filters
@app.get("/analytics/all")
def get_all_data(
    device_id: str | None = Query(None, description="Filter by device identifier"),
    building: str | None = Query(None, description="Filter by building name"),
    location: str | None = Query(None, description="Filter by location"),
    property_id: str | None = Query(None, description="Filter by property type"),
    days: int = Query(7, description="Number of days to look back")
):
    """Get all sensor data with optional filters"""
    try:
        query_api = get_query_api()
        
        # Build dynamic Flux query based on filters
        filter_parts = []
        filter_parts.append('r._measurement == "sensor_data"')
        
        if device_id:
            filter_parts.append('r.device_id == "{0}"'.format(device_id))
        if building:
            filter_parts.append('r.building == "{0}"'.format(building))
        if location:
            filter_parts.append('r.location == "{0}"'.format(location))
        if property_id:
            filter_parts.append('r.property_id == "{0}"'.format(property_id))
        
        filter_expression = ' and '.join(filter_parts)
        
        flux_query = f"""
        from(bucket: "{BUCKET}")
        |> range(start: -{days}d)
        |> filter(fn: (r) => {filter_expression})
        |> sort(columns: ["_time"], desc: true)
        """
        
        tables = query_api.query(flux_query, org=ORG)
        
        results = []
        for table in tables:
            for record in table.records:
                record_dict = {
                    "time": record.get_time().isoformat(),
                    "device_id": record.values.get("device_id"),
                    "property_id": record.values.get("property_id"),
                    "value": record.get_value()
                }
                
                optional_fields = ["building", "location", "status"]
                for field in optional_fields:
                    if record.values.get(field) is not None:
                        record_dict[field] = record.values.get(field)
                
                results.append(record_dict)
        
        return {
            "count": len(results),
            "filters_used": {
                "device_id": device_id,
                "building": building,
                "location": location,
                "property_id": property_id
            },
            "data": results
        }
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 5. Get history by device
@app.get("/analytics/history")
def get_history(
    device_id: str,
    property_id: str | None = Query(None, description="Filter by property (field) name"),
    days: int = Query(7, description="Number of days to look back")
):
    """Get sensor data history for a specific device"""
    try:
        query_api = get_query_api()
        
        # Build dynamic query - get all fields if no property_id specified
        if property_id:
            field_filter = f'r._field == "{property_id}"'
        else:
            field_filter = 'true'  # Get all fields
        
        query = f"""
        from(bucket: "{BUCKET}")
          |> range(start: -{days}d)
          |> filter(fn: (r) => r._measurement == "sensor_data")
          |> filter(fn: (r) => r.device_id == "{device_id}")
          |> filter(fn: (r) => {field_filter})
        """
        
        tables = query_api.query(query, org=ORG)
        
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "time": record.get_time().isoformat(),
                    "device_id": record.values.get("device_id"),
                    "property_id": record.values.get("property_id"),
                    "field": record.get_field(),
                    "value": record.get_value()
                })
        
        return {
            "device_id": device_id,
            "property_id": property_id,
            "count": len(results),
            "data": results
        }
    
    except Exception as e:
        logger.error(f"History query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
