CREATE TABLE IF NOT EXISTS dim_store (
    store_key BIGSERIAL PRIMARY KEY,
    store_code TEXT NOT NULL UNIQUE,
    store_name TEXT NOT NULL,
    city TEXT
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key BIGSERIAL PRIMARY KEY,
    product_sku TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT,
    brand TEXT
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key BIGSERIAL PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_name TEXT,
    customer_email TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    quarter SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name TEXT NOT NULL,
    week SMALLINT NOT NULL,
    day SMALLINT NOT NULL,
    day_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_key BIGSERIAL PRIMARY KEY,
    transaction_id TEXT NOT NULL UNIQUE,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    store_key BIGINT NOT NULL REFERENCES dim_store(store_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    customer_key BIGINT REFERENCES dim_customer(customer_key),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    unit_cost NUMERIC(12, 2) NOT NULL CHECK (unit_cost >= 0),
    revenue NUMERIC(14, 2) NOT NULL,
    profit NUMERIC(14, 2) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_sales_store ON fact_sales(store_key);
CREATE INDEX IF NOT EXISTS idx_sales_product ON fact_sales(product_key);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON fact_sales(customer_key);

CREATE TABLE IF NOT EXISTS fact_inventory_snapshot (
    inventory_key BIGSERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    store_key BIGINT NOT NULL REFERENCES dim_store(store_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    on_hand_qty INTEGER NOT NULL CHECK (on_hand_qty >= 0),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
    unit_cost NUMERIC(12, 2) NOT NULL CHECK (unit_cost >= 0),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (snapshot_date, store_key, product_key)
);

CREATE INDEX IF NOT EXISTS idx_inventory_date ON fact_inventory_snapshot(snapshot_date);

CREATE OR REPLACE VIEW v_inventory_latest AS
SELECT DISTINCT ON (i.store_key, i.product_key)
    i.snapshot_date,
    i.store_key,
    i.product_key,
    i.on_hand_qty,
    i.reorder_point,
    i.unit_cost
FROM fact_inventory_snapshot i
ORDER BY i.store_key, i.product_key, i.snapshot_date DESC;
