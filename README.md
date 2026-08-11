# 🛍️ RetailPulse

> An end-to-end retail analytics dashboard for monitoring sales, profitability, inventory health, customer behavior, and store performance.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458)
![Altair](https://img.shields.io/badge/Altair-Visualization-orange)

---

## 📊 Overview

RetailPulse is a retail business intelligence application built with Python and Streamlit.

It provides a centralized dashboard for analyzing:

- 💰 Revenue
- 📈 Gross profit
- 📊 Profit margins
- 🧾 Transactions
- 📦 Inventory
- 🚨 Low-stock alerts
- 👥 Customer segments
- 🛒 Product performance
- 🏪 Store performance

The project demonstrates an end-to-end data analytics workflow from data ingestion and storage to business intelligence and visualization.

---

## ✨ Features

### 📈 Sales Overview

- Revenue tracking
- Gross profit
- Profit margin
- Transaction volume
- Units sold
- Sales and profit trends
- Top products by revenue
- Store revenue comparison

### 📦 Inventory Intelligence

- Inventory valuation
- Stock levels
- Out-of-stock detection
- Low-stock alerts
- Suggested reorder quantities
- Days of inventory cover
- Average daily sales velocity

### 👥 Customer Intelligence

RetailPulse uses RFM analysis:

- Recency
- Frequency
- Monetary value

Customers are grouped into business-oriented segments such as:

- Champions
- Loyal customers
- At risk
- Hibernating
- Other customer segments

### 🏪 Product & Store Analysis

Interactive tables provide detailed analysis of:

- Product performance
- Store performance
- Revenue
- Profit
- Units sold
- Inventory position

---

## 🏗️ Architecture

```text
                RetailPulse
                     │
                     ▼
              Data Ingestion
                     │
                     ▼
              Data Warehouse
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     PostgreSQL           Sample Data Mode
          │
          ▼
      Analytics Layer
          │
          ▼
      Streamlit App
          │
    ┌─────┼─────┬─────────┐
    ▼     ▼     ▼         ▼
  Sales Inventory Customers Products