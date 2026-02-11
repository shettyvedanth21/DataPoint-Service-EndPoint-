from fastapi import APIRouter, Query
from influxdb_client import InfluxDBClient
from typing import Optional
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# -------------------------
# InfluxDB Config (same as ingest)
# -------------------------
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "6_JnebAkyomoHqDgw7iyjtQSjhyb-bJ4codYsZhtb02akUIKpe1LSEa7QI8-5qxnBC06hzjkBhnvKAwswiNbYA=="
INFLUX_ORG = "ai_factory"
INFLUX_BUCKET = "machine_data"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()

# -------------------------
# Generic analytics function
# -------------------------
def get_metric(metric: str, start: str = "-24h", end: str = "now()", device_id: Optional[str] = None):
    # Build the time range
    time_range = f"start: {start}"
    if end and end != "now()":
        time_range = f"start: {start}, stop: {end}"
    
    # Build filters
    filters = [
        f'r._measurement == "air_compressor"',
        f'r._field == "{metric}"'
    ]
    
    if device_id:
        filters.append(f'r.device_id == "{device_id}"')
    
    filter_clause = " |> ".join([f'filter(fn: (r) => {f})' for f in filters])
    
    query = f'from(bucket: "{INFLUX_BUCKET}") |> range({time_range}) |> {filter_clause} |> sort(columns: ["_time"])'

    tables = query_api.query(query, org=INFLUX_ORG)

    results = []
    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time(),
                "value": record.get_value()
            })

    return results


def get_metric_trend(
    metric: str,
    device_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None
) -> dict:
    """Fetch time-series trend data for a metric."""
    # Default to last 24 hours
    if start is None:
        start = datetime.now(timezone.utc) - timedelta(hours=24)
    if end is None:
        end = datetime.now(timezone.utc)
    
    # Build Flux query
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    filters = [
        f'r._measurement == "air_compressor"',
        f'r._field == "{metric}"'
    ]
    
    if device_id:
        filters.append(f'r.device_id == "{device_id}"')
    
    filter_clause = " |> ".join([f'filter(fn: (r) => {f})' for f in filters])
    
    query = f'from(bucket: "{INFLUX_BUCKET}") |> range(start: {start_str}, stop: {end_str}) |> {filter_clause} |> sort(columns: ["_time"])'

    try:
        tables = query_api.query(query, org=INFLUX_ORG)
    except Exception as e:
        # Return empty response on query error
        return {"device_id": device_id or "", "data": []}

    results = []
    for table in tables:
        for record in table.records:
            timestamp = record.get_time()
            if timestamp:
                # Convert to ISO format
                if hasattr(timestamp, 'isoformat'):
                    timestamp = timestamp.isoformat()
                results.append({
                    "timestamp": timestamp,
                    "value": record.get_value()
                })

    return {"device_id": device_id or "", "data": results}

# -------------------------
# APIs
# -------------------------
@router.get("/energy")
def energy_chart():
    return get_metric("energy")

@router.get("/power")
def power_chart():
    return get_metric("power")

@router.get("/voltage")
def voltage_chart():
    return get_metric("voltage")


# -------------------------
# Trend Endpoints
# -------------------------
@router.get("/energy-trend")
def energy_trend(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    start: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end: Optional[datetime] = Query(None, description="End time (ISO format)")
):
    """
    Get energy trend data from InfluxDB.
    
    Returns time-series data with timestamps and values.
    Defaults to last 24 hours if no time range specified.
    """
    return get_metric_trend("energy", device_id, start, end)


@router.get("/power-trend")
def power_trend(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    start: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end: Optional[datetime] = Query(None, description="End time (ISO format)")
):
    """
    Get power trend data from InfluxDB.
    
    Returns time-series data with timestamps and values.
    Defaults to last 24 hours if no time range specified.
    """
    return get_metric_trend("power", device_id, start, end)
