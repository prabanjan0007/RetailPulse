# 🚀 RetailPulse

RetailPulse is a retail analytics and business intelligence dashboard designed to provide a single control room for monitoring sales, profitability, inventory health, and customer intelligence.

It combines a PostgreSQL data warehouse, FastAPI backend, analytics layer, and Streamlit dashboard into one end-to-end retail analytics application.

---

## 📊 Features

### 💰 Sales Overview
- Revenue tracking
- Gross profit analysis
- Profit margin calculation
- Transaction and unit tracking
- Sales and profit trends
- Top products by revenue
- Store revenue comparison

### 📦 Inventory & Alerts
- Total inventory valuation
- Active SKU/store monitoring
- Out-of-stock detection
- Low-stock alert queue
- Reorder point monitoring
- Suggested replenishment quantities
- Days-of-cover analysis

### 👥 Customer Intelligence
- RFM customer segmentation
- Recency analysis
- Purchase frequency
- Customer monetary value
- Customer segment summaries
- Customer-level RFM analysis

### 🏪 Product & Store Analysis
- Product performance analysis
- Store performance comparison
- Revenue and profit by store
- Units sold
- Transaction analysis

---

## 🏗️ Architecture

```text
                 ┌─────────────────────┐
                 │     Sample Data     │
                 │      CSV Files      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Data Ingestion   │
                 │   Python / CLI      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     PostgreSQL      │
                 │    Data Warehouse   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Analytics Layer    │
                 │      Python         │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
       ┌──────────────────┐   ┌──────────────────┐
       │    FastAPI       │   │    Streamlit     │
       │      API         │   │    Dashboard     │
       └──────────────────┘   └──────────────────┘