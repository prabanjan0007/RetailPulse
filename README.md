# RetailPulse — Sales & Inventory Intelligence

RetailPulse is a portfolio-ready retail analytics project that helps managers improve sales, protect profit, and avoid stock-outs.

## Features

- **CSV and API ingestion** for sales and inventory data
- **ETL validation** for required columns, dates, quantities, prices, and duplicate sales lines
- **PostgreSQL warehouse** with product, store, customer, and date dimensions
- **Sales and profit dashboard** with time, store, and product analysis
- **Inventory dashboard** with latest inventory value and out-of-stock visibility
- **Low-stock alerts** with 30-day sales velocity, days of cover, severity, and suggested order quantity
- **RFM customer segmentation**: Champions, Loyal, New, At risk, Hibernating, and Potential loyalists
- **REST API** for loading records and embedding analytics in another application

## Run it locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d
python -m retailpulse.cli load-samples
streamlit run retailpulse/dashboard.py
```

Open the dashboard at `http://localhost:8501`.

To use the API, start a separate terminal:

```powershell
uvicorn retailpulse.api:app --reload
```

The interactive API docs are at `http://localhost:8000/docs`.

## Bring your own CSVs

```powershell
python -m retailpulse.cli load --sales path\to\sales.csv --inventory path\to\inventory.csv
```

Sales needs `transaction_id`, `sale_date`, `store_code`, `product_sku`, `quantity`, `unit_price`, and `unit_cost`. `customer_id` is optional but required for RFM segmentation.

Inventory needs `snapshot_date`, `store_code`, `product_sku`, `on_hand_qty`, `reorder_point`, and `unit_cost`.

Optional descriptive fields include store name/city, product name/category/brand, and customer name/email. The included files in `data/sample` show the complete format.

## API endpoints

| Endpoint | Purpose |
| --- | --- |
| `POST /ingest/sales` | Load a JSON list of sale records |
| `POST /ingest/inventory` | Load a JSON list of inventory records |
| `GET /analytics/summary` | Revenue, profit, margin, units, transactions |
| `GET /analytics/products` | Product performance |
| `GET /analytics/stores` | Store performance |
| `GET /analytics/rfm` | Customer RFM segments |
| `GET /alerts/low-stock` | Replenishment alert queue |

## Structure

```text
retailpulse/
  ingest.py       CSV/API transformation and validation
  warehouse.py    Dimension and fact-table loaders
  analytics.py    KPI, inventory alert, and RFM queries
  dashboard.py    Streamlit manager dashboard
  api.py          FastAPI service
sql/schema.sql    PostgreSQL warehouse schema
data/sample/      Starter sales and inventory data
```
