from fastapi import APIRouter
from app.influx_config import query_api, ORG, BUCKET

router = APIRouter(prefix="/analytics", tags=["Analytics"])
# Analytics GET endpoints intentionally removed
# Only POST /analytics/datapoint remains in datapoint_router.py
