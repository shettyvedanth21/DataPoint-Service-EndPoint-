
It is an industrial IoT backend service that collects, stores, and retrieves machine sensor data using FastAPI and InfluxDB.

Features:
* Real-time machine sensor data ingestion
* Structured storage using InfluxDB time- series database
* Latest sensor value retrieval
* Historical data access per device


Technology Stack
Backend:
* Python
* FastAPI
* Pydantic
* Uvicorn

Database:
* InfluxDB (Time-Series Database)

Data Communication:
* MQTT Publisher (sensor simulation)
* JSON-based API communication


InfluxDB Configuration:
Organization:ai_factory
Bucket:machine_data
Measurement:sensor_data

Run Server:
uvicorn app.main:app --reload
Server runs at:http://127.0.0.1:8000
APIDocumentation:http://127.0.0.1:8000/docs

Data Model
Tags:
* device_id → machine identifier
* property_id → sensor type (temperature, voltage, etc.)
* building → building name
* location → device location
* status → operational state

Fields:
* value → sensor reading
* battery_level → battery percentage
* raw_value → raw sensor output
* signal_strength → network signal
* error_code → device error code
* calibration_offset → calibration adjustment

API Endpoints
POST /analytics/datapoint
Write machine sensor datapoint

GET /analytics/latest?device_id=D01&property_id=temperature
Get latest value of a device property

GET /analytics/history?device_id=D01
Get device data history

GET /analytics/all
Get all machine sensor data




