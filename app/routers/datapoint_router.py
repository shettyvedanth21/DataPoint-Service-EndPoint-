"""
DataPoint Router Module
Handles sensor ingestion and analytics queries.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from influxdb_client import Point, WritePrecision

from app.influx_config import write_api, query_api, ORG, BUCKET

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------- INPUT MODELS ----------------

class DataPointInput(BaseModel):
    device_id: str = Field(..., min_length=1)
    property_id: str = Field(..., min_length=1)
    value: float

    building: str | None = None
    location: str | None = None
    status: str | None = None

    battery_level: float | None = None
    raw_value: float | None = None
    signal_strength: float | None = None
    error_code: int | None = None
    calibration_offset: float | None = None

    @field_validator('device_id', 'property_id')
    @classmethod
    def not_empty(cls, v):
        return v.strip()


class DataPointResponse(BaseModel):
    status: str
    device_id: str
    property_id: str
    value: float


# ---------------- WRITE DATA ----------------

@router.post("/datapoint", response_model=DataPointResponse)
def write_datapoint(data: DataPointInput):
    try:
        point = (
            Point("sensor_data")
            .tag("device_id", data.device_id)
            .tag("property_id", data.property_id)
            .field("value", float(data.value))
            .time(datetime.now(timezone.utc), WritePrecision.NS)
        )

        if data.building:
            point = point.tag("building", data.building)
        if data.location:
            point = point.tag("location", data.location)
        if data.status:
            point = point.tag("status", data.status)

        if data.battery_level is not None:
            point = point.field("battery_level", float(data.battery_level))
        if data.raw_value is not None:
            point = point.field("raw_value", float(data.raw_value))
        if data.signal_strength is not None:
            point = point.field("signal_strength", float(data.signal_strength))
        if data.error_code is not None:
            point = point.field("error_code", int(data.error_code))
        if data.calibration_offset is not None:
            point = point.field("calibration_offset", float(data.calibration_offset))

        write_api.write(bucket=BUCKET, org=ORG, record=point)

        return DataPointResponse(
            status="success",
            device_id=data.device_id,
            property_id=data.property_id,
            value=data.value
        )

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="Failed to write datapoint")


# ---------------- GET LATEST ----------------

@router.get("/all")
def get_all_data():
    try:
        flux_query = f'''
        from(bucket: "{BUCKET}")
        |> range(start: -7d)
        |> filter(fn: (r) => r["_measurement"] == "sensor_data")
        |> filter(fn: (r) => r["_field"] == "value")
        |> sort(columns: ["_time"], desc: true)
        '''

        tables = query_api.query(flux_query, org=ORG)

        result = []
        for table in tables:
            for record in table.records:
                result.append({
                    "time": record.get_time(),
                    "device_id": record.values.get("device_id"),
                    "property_id": record.values.get("property_id"),
                    "value": record.get_value()
                })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- GET HISTORY ----------------

@router.get("/history")
def get_history(device_id: str):
    try:
        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> filter(fn: (r) => r["_field"] == "value")
        '''

        tables = query_api.query(query)

        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "device_id": record.values.get("device_id"),
                    "property_id": record.values.get("property_id"),
                    "value": record.get_value()
                })

        return results

    except Exception:
        raise HTTPException(status_code=500, detail="Query execution failed")


# ---------------- GET ALL ----------------

@router.get("/all")
def get_all_data():
    try:
        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> filter(fn: (r) => r["_field"] == "value")
        '''

        tables = query_api.query(query)

        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "device_id": record.values.get("device_id"),
                    "property_id": record.values.get("property_id"),
                    "value": record.get_value()
                })

        return results

    except Exception:
        raise HTTPException(status_code=500, detail="Query execution failed")
