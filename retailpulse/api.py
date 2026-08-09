from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from retailpulse import analytics
from retailpulse.db import get_connection, initialize_schema
from retailpulse.ingest import normalize_inventory, normalize_sales, records_to_frame
from retailpulse.warehouse import load_inventory, load_sales

app = FastAPI(title="RetailPulse API", version="1.0.0", description="Sales and inventory intelligence API")


@app.get("/health")
def health() -> dict:
    try:
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok", "service": "retailpulse"}
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {error}") from error


@app.post("/admin/initialize")
def initialize() -> dict:
    try:
        initialize_schema()
        return {"status": "initialized"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/ingest/sales")
def ingest_sales(records: list[dict]) -> dict:
    try:
        loaded = load_sales(normalize_sales(records_to_frame(records)))
        return {"status": "loaded", "dataset": "sales", "rows": loaded}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/ingest/inventory")
def ingest_inventory(records: list[dict]) -> dict:
    try:
        loaded = load_inventory(normalize_inventory(records_to_frame(records)))
        return {"status": "loaded", "dataset": "inventory", "rows": loaded}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/analytics/summary")
def summary(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    store_code: str | None = Query(None),
) -> dict:
    return jsonable_encoder(analytics.sales_summary(start_date, end_date, store_code))


@app.get("/analytics/products")
def products(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    store_code: str | None = Query(None),
) -> list[dict]:
    return jsonable_encoder(analytics.product_performance(start_date, end_date, store_code).to_dict("records"))


@app.get("/analytics/stores")
def stores(start_date: date | None = Query(None), end_date: date | None = Query(None)) -> list[dict]:
    return jsonable_encoder(analytics.store_performance(start_date, end_date).to_dict("records"))


@app.get("/analytics/rfm")
def rfm() -> list[dict]:
    return jsonable_encoder(analytics.rfm_segments().to_dict("records"))


@app.get("/alerts/low-stock")
def low_stock() -> list[dict]:
    return jsonable_encoder(analytics.low_stock_alerts().to_dict("records"))
