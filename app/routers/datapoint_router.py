
import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from influxdb_client import Point, WritePrecision
from app.influx_config import write_api, query_api, ORG, BUCKET
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# GET HISTORY BY DEVICE
@router.get("/history")
def get_history(device_id: str):
  
    try:
        query = f"""
        from(bucket: "{BUCKET}")
          |> range(start: -7d)
          |> filter(fn: (r) => r._measurement == "sensor_data")
          |> filter(fn: (r) => r.device_id == "{device_id}")
          |> filter(fn: (r) => r._field == "current" or r._field == "voltage" or r._field == "temperature")
        """
        logger.info(f"History query: {query}")
        tables = query_api.query(query, org=ORG)
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "time": record.get_time().isoformat(),
                    "device_id": record.values.get("device_id"),
                    "property_id": record.values.get("property_id"),
                    "value": record.get_value()
                })

        return {
            "device_id": device_id,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"History query error: {e}")
        raise HTTPException(status_code=500, detail="Query execution failed")

