from fastapi import FastAPI
from app.influx_config import query_api, BUCKET

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Machine Analytics API running"}


@app.get("/temperature")
def get_temperature():
    query = f'''
    from(bucket: "{BUCKET}")
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
