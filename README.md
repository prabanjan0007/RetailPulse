# 🚀 RetailPulse

RetailPulse is a retail analytics and business intelligence dashboard designed to provide a single control room for monitoring **sales, profitability, inventory health, and customer intelligence**.

It combines a **PostgreSQL data warehouse, FastAPI backend, Python analytics layer, and Streamlit dashboard** into one end-to-end retail analytics application.

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
- Units sold analysis
- Transaction analysis

---

## 🏗️ Architecture

```text
                 ┌─────────────────────┐
                 │    Sample Data      │
                 │      CSV Files      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Data Ingestion    │
                 │    Python / CLI     │
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
                 │    Analytics Layer  │
                 │       Python        │
                 └──────────┬──────────┘
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
        ┌─────────────────┐   ┌─────────────────┐
        │     FastAPI     │   │    Streamlit    │
        │       API       │   │    Dashboard    │
        └─────────────────┘   └─────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Programming | Python |
| Dashboard | Streamlit |
| Backend API | FastAPI |
| Database | PostgreSQL |
| Data Analysis | Pandas |
| Data Visualization | Streamlit Charts |
| Containerization | Docker |
| Database Driver | psycopg |
| Version Control | Git & GitHub |

---

## 📁 Project Structure

```text
RetailPulse/
│
├── retailpulse/
│   ├── __init__.py
│   ├── analytics.py
│   ├── api.py
│   ├── cli.py
│   ├── config.py
│   ├── dashboard.py
│   ├── db.py
│   ├── ingest.py
│   └── warehouse.py
│
├── data/
│
├── sql/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
└── requirements.txt
```

---

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd RetailPulse
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL with Docker

```bash
docker compose up -d
```

### 5. Load sample data

```bash
python -m retailpulse.cli load-samples
```

### 6. Start the Streamlit dashboard

```bash
python -m streamlit run .\retailpulse\dashboard.py
```

The dashboard will be available at:

```text
http://localhost:8501
```

---

## 📈 Dashboard

RetailPulse provides an interactive dashboard containing:

- Sales overview
- Revenue and profit trends
- Product performance
- Store performance
- Inventory monitoring
- Low-stock alerts
- Customer RFM segmentation
- Product and store analysis

---

## 🗄️ Data Pipeline

The project follows an end-to-end analytics workflow:

```text
CSV Sample Data
      ↓
Data Ingestion
      ↓
PostgreSQL
      ↓
Analytics Layer
      ↓
FastAPI / Streamlit
      ↓
Business Insights
```

This architecture demonstrates how raw retail data can be transformed into actionable business intelligence.

---

## 🧠 Analytics

### RFM Customer Segmentation

RetailPulse uses **RFM analysis** to understand customer behavior:

- **Recency** — How recently a customer purchased
- **Frequency** — How often a customer purchases
- **Monetary Value** — How much a customer spends

These metrics are used to create customer segments and identify valuable, at-risk, and inactive customers.

### Inventory Intelligence

The dashboard also calculates inventory indicators such as:

- Current inventory value
- Stock availability
- Reorder requirements
- Average daily sales
- Days of inventory coverage

---

## 🐳 Docker

PostgreSQL can be launched using Docker Compose:

```bash
docker compose up -d
```

Check running containers:

```bash
docker ps
```

Stop the database:

```bash
docker compose down
```

---

## 🔐 Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=retailpulse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

**Never commit real passwords or secrets to GitHub.**

---

## 🎯 Project Goals

RetailPulse was built to demonstrate practical skills in:

- Python programming
- Data analytics
- SQL and PostgreSQL
- Data warehousing
- ETL/data ingestion
- Business intelligence
- Dashboard development
- REST API development
- Docker
- Git and GitHub
- Customer segmentation
- Inventory analytics

---

## 🚀 Future Improvements

Potential future enhancements include:

- [ ] Cloud deployment
- [ ] Authentication and user roles
- [ ] Advanced forecasting
- [ ] Automated email alerts
- [ ] Real-time data ingestion
- [ ] Machine-learning based demand prediction
- [ ] Advanced sales forecasting
- [ ] Automated dashboard refresh
- [ ] CI/CD pipeline
- [ ] Unit and integration testing

---

## 👨‍💻 Author

**Prabanjan**

AI & Data Science Student

This project is part of a portfolio focused on building practical **data analytics, data engineering, and AI applications**.

---

## 📄 License

This project is intended for educational and portfolio purposes.