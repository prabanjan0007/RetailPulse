from __future__ import annotations

from datetime import date

import pandas as pd

from retailpulse.db import get_connection


def load_sales(frame: pd.DataFrame) -> int:
    """Upsert cleaned sale lines and their dimensions into PostgreSQL."""
    if frame.empty:
        return 0
    with get_connection() as connection, connection.cursor() as cursor:
        _upsert_stores(cursor, frame)
        _upsert_products(cursor, frame)
        _upsert_customers(cursor, frame)
        _upsert_dates(cursor, frame["sale_date"].unique())
        store_keys = _key_map(cursor, "dim_store", "store_code", "store_key")
        product_keys = _key_map(cursor, "dim_product", "product_sku", "product_key")
        customer_keys = _key_map(cursor, "dim_customer", "customer_id", "customer_key")
        for row in frame.to_dict("records"):
            cursor.execute(
                """
                INSERT INTO fact_sales (
                    transaction_id, date_key, store_key, product_key, customer_key,
                    quantity, unit_price, unit_cost, revenue, profit
                ) VALUES (
                    %(transaction_id)s, %(date_key)s, %(store_key)s, %(product_key)s, %(customer_key)s,
                    %(quantity)s, %(unit_price)s, %(unit_cost)s, %(revenue)s, %(profit)s
                )
                ON CONFLICT (transaction_id) DO UPDATE SET
                    date_key = EXCLUDED.date_key,
                    store_key = EXCLUDED.store_key,
                    product_key = EXCLUDED.product_key,
                    customer_key = EXCLUDED.customer_key,
                    quantity = EXCLUDED.quantity,
                    unit_price = EXCLUDED.unit_price,
                    unit_cost = EXCLUDED.unit_cost,
                    revenue = EXCLUDED.revenue,
                    profit = EXCLUDED.profit,
                    loaded_at = now()
                """,
                {
                    "transaction_id": row["transaction_id"],
                    "date_key": _date_key(row["sale_date"]),
                    "store_key": store_keys[row["store_code"]],
                    "product_key": product_keys[row["product_sku"]],
                    "customer_key": customer_keys.get(row["customer_id"]),
                    "quantity": int(row["quantity"]),
                    "unit_price": float(row["unit_price"]),
                    "unit_cost": float(row["unit_cost"]),
                    "revenue": float(row["revenue"]),
                    "profit": float(row["profit"]),
                },
            )
        connection.commit()
    return len(frame)


def load_inventory(frame: pd.DataFrame) -> int:
    """Upsert inventory snapshots and their dimensions into PostgreSQL."""
    if frame.empty:
        return 0
    with get_connection() as connection, connection.cursor() as cursor:
        _upsert_stores(cursor, frame)
        _upsert_products(cursor, frame)
        store_keys = _key_map(cursor, "dim_store", "store_code", "store_key")
        product_keys = _key_map(cursor, "dim_product", "product_sku", "product_key")
        for row in frame.to_dict("records"):
            cursor.execute(
                """
                INSERT INTO fact_inventory_snapshot (
                    snapshot_date, store_key, product_key, on_hand_qty, reorder_point, unit_cost
                ) VALUES (%(snapshot_date)s, %(store_key)s, %(product_key)s, %(on_hand_qty)s,
                          %(reorder_point)s, %(unit_cost)s)
                ON CONFLICT (snapshot_date, store_key, product_key) DO UPDATE SET
                    on_hand_qty = EXCLUDED.on_hand_qty,
                    reorder_point = EXCLUDED.reorder_point,
                    unit_cost = EXCLUDED.unit_cost,
                    loaded_at = now()
                """,
                {
                    "snapshot_date": row["snapshot_date"],
                    "store_key": store_keys[row["store_code"]],
                    "product_key": product_keys[row["product_sku"]],
                    "on_hand_qty": int(row["on_hand_qty"]),
                    "reorder_point": int(row["reorder_point"]),
                    "unit_cost": float(row["unit_cost"]),
                },
            )
        connection.commit()
    return len(frame)


def _upsert_stores(cursor, frame: pd.DataFrame) -> None:
    rows = frame[["store_code", "store_name", "city"]].drop_duplicates().to_dict("records")
    cursor.executemany(
        """
        INSERT INTO dim_store (store_code, store_name, city)
        VALUES (%(store_code)s, %(store_name)s, %(city)s)
        ON CONFLICT (store_code) DO UPDATE SET
            store_name = EXCLUDED.store_name,
            city = EXCLUDED.city
        """,
        rows,
    )


def _upsert_products(cursor, frame: pd.DataFrame) -> None:
    rows = frame[["product_sku", "product_name", "category", "brand"]].drop_duplicates().to_dict("records")
    cursor.executemany(
        """
        INSERT INTO dim_product (product_sku, product_name, category, brand)
        VALUES (%(product_sku)s, %(product_name)s, %(category)s, %(brand)s)
        ON CONFLICT (product_sku) DO UPDATE SET
            product_name = EXCLUDED.product_name,
            category = EXCLUDED.category,
            brand = EXCLUDED.brand
        """,
        rows,
    )


def _upsert_customers(cursor, frame: pd.DataFrame) -> None:
    customers = frame.dropna(subset=["customer_id"])
    if customers.empty:
        return
    rows = customers[["customer_id", "customer_name", "customer_email"]].drop_duplicates().to_dict("records")
    cursor.executemany(
        """
        INSERT INTO dim_customer (customer_id, customer_name, customer_email)
        VALUES (%(customer_id)s, %(customer_name)s, %(customer_email)s)
        ON CONFLICT (customer_id) DO UPDATE SET
            customer_name = COALESCE(EXCLUDED.customer_name, dim_customer.customer_name),
            customer_email = COALESCE(EXCLUDED.customer_email, dim_customer.customer_email)
        """,
        rows,
    )


def _upsert_dates(cursor, values) -> None:
    dates = sorted({value for value in values if value is not None})
    rows = [
        {
            "date_key": _date_key(value),
            "full_date": value,
            "year": value.year,
            "quarter": (value.month - 1) // 3 + 1,
            "month": value.month,
            "month_name": value.strftime("%B"),
            "week": value.isocalendar().week,
            "day": value.day,
            "day_name": value.strftime("%A"),
        }
        for value in dates
    ]
    cursor.executemany(
        """
        INSERT INTO dim_date (date_key, full_date, year, quarter, month, month_name, week, day, day_name)
        VALUES (%(date_key)s, %(full_date)s, %(year)s, %(quarter)s, %(month)s, %(month_name)s,
                %(week)s, %(day)s, %(day_name)s)
        ON CONFLICT (date_key) DO NOTHING
        """,
        rows,
    )


def _key_map(cursor, table: str, code_column: str, key_column: str) -> dict[str, int]:
    cursor.execute(f"SELECT {code_column}, {key_column} FROM {table}")
    return {row[code_column]: row[key_column] for row in cursor.fetchall()}


def _date_key(value: date) -> int:
    return int(value.strftime("%Y%m%d"))
