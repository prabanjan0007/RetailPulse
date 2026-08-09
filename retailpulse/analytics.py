from __future__ import annotations

from datetime import date

import pandas as pd

from retailpulse.db import get_connection


def query_frame(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(sql, params or {})
        rows = cursor.fetchall()
    return pd.DataFrame(rows)


def sales_summary(start_date: date | None = None, end_date: date | None = None, store_code: str | None = None) -> dict:
    where, params = _sales_filters(start_date, end_date, store_code)
    frame = query_frame(
        f"""
        SELECT COALESCE(SUM(fs.revenue), 0) AS revenue,
               COALESCE(SUM(fs.profit), 0) AS profit,
               COUNT(DISTINCT fs.transaction_id) AS transactions,
               COALESCE(SUM(fs.quantity), 0) AS units,
               CASE WHEN SUM(fs.revenue) > 0
                    THEN SUM(fs.profit) / SUM(fs.revenue) * 100 ELSE 0 END AS margin_pct
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        JOIN dim_store ds ON ds.store_key = fs.store_key
        {where}
        """,
        params,
    )
    return frame.iloc[0].to_dict()


def sales_trend(start_date: date | None = None, end_date: date | None = None, store_code: str | None = None) -> pd.DataFrame:
    where, params = _sales_filters(start_date, end_date, store_code)
    return query_frame(
        f"""
        SELECT dd.full_date AS date, SUM(fs.revenue) AS revenue, SUM(fs.profit) AS profit,
               SUM(fs.quantity) AS units
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        JOIN dim_store ds ON ds.store_key = fs.store_key
        {where}
        GROUP BY dd.full_date
        ORDER BY dd.full_date
        """,
        params,
    )


def product_performance(start_date: date | None = None, end_date: date | None = None, store_code: str | None = None) -> pd.DataFrame:
    where, params = _sales_filters(start_date, end_date, store_code)
    return query_frame(
        f"""
        SELECT dp.product_sku, dp.product_name, dp.category, dp.brand,
               SUM(fs.quantity) AS units_sold, SUM(fs.revenue) AS revenue, SUM(fs.profit) AS profit,
               CASE WHEN SUM(fs.revenue) > 0 THEN SUM(fs.profit) / SUM(fs.revenue) * 100 ELSE 0 END AS margin_pct
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        JOIN dim_store ds ON ds.store_key = fs.store_key
        JOIN dim_product dp ON dp.product_key = fs.product_key
        {where}
        GROUP BY dp.product_sku, dp.product_name, dp.category, dp.brand
        ORDER BY revenue DESC
        """,
        params,
    )


def store_performance(start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
    where, params = _sales_filters(start_date, end_date, None)
    return query_frame(
        f"""
        SELECT ds.store_code, ds.store_name, ds.city, SUM(fs.revenue) AS revenue,
               SUM(fs.profit) AS profit, SUM(fs.quantity) AS units_sold,
               COUNT(DISTINCT fs.transaction_id) AS transactions
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        JOIN dim_store ds ON ds.store_key = fs.store_key
        {where}
        GROUP BY ds.store_code, ds.store_name, ds.city
        ORDER BY revenue DESC
        """,
        params,
    )


def inventory_overview() -> pd.DataFrame:
    return query_frame(
        """
        SELECT ds.store_code, ds.store_name, ds.city, dp.product_sku, dp.product_name,
               dp.category, dp.brand, i.snapshot_date, i.on_hand_qty, i.reorder_point,
               i.unit_cost, i.on_hand_qty * i.unit_cost AS inventory_value
        FROM v_inventory_latest i
        JOIN dim_store ds ON ds.store_key = i.store_key
        JOIN dim_product dp ON dp.product_key = i.product_key
        ORDER BY inventory_value DESC
        """
    )


def low_stock_alerts() -> pd.DataFrame:
    return query_frame(
        """
        WITH latest_sale AS (
            SELECT MAX(full_date) AS max_date FROM dim_date
        ), velocity AS (
            SELECT fs.store_key, fs.product_key,
                   SUM(fs.quantity)::numeric / GREATEST(COUNT(DISTINCT dd.full_date), 1) AS avg_daily_units
            FROM fact_sales fs
            JOIN dim_date dd ON dd.date_key = fs.date_key
            CROSS JOIN latest_sale ls
            WHERE dd.full_date >= ls.max_date - INTERVAL '29 days'
            GROUP BY fs.store_key, fs.product_key
        )
        SELECT ds.store_code, ds.store_name, dp.product_sku, dp.product_name, dp.category,
               i.snapshot_date, i.on_hand_qty, i.reorder_point,
               COALESCE(ROUND(v.avg_daily_units, 2), 0) AS avg_daily_units,
               CASE WHEN COALESCE(v.avg_daily_units, 0) > 0
                    THEN ROUND(i.on_hand_qty / v.avg_daily_units, 1) END AS days_of_cover,
               CEIL(GREATEST(i.reorder_point - i.on_hand_qty, 0) + COALESCE(v.avg_daily_units, 0) * 7) AS suggested_order_qty,
               CASE WHEN i.on_hand_qty = 0 THEN 'Critical'
                    WHEN i.on_hand_qty <= i.reorder_point / 2.0 THEN 'High'
                    ELSE 'Medium' END AS severity
        FROM v_inventory_latest i
        JOIN dim_store ds ON ds.store_key = i.store_key
        JOIN dim_product dp ON dp.product_key = i.product_key
        LEFT JOIN velocity v ON v.store_key = i.store_key AND v.product_key = i.product_key
        WHERE i.on_hand_qty <= i.reorder_point
        ORDER BY CASE WHEN i.on_hand_qty = 0 THEN 1 WHEN i.on_hand_qty <= i.reorder_point / 2.0 THEN 2 ELSE 3 END,
                 days_of_cover NULLS LAST, i.on_hand_qty ASC
        """
    )


def rfm_segments() -> pd.DataFrame:
    return query_frame(
        """
        WITH customer_metrics AS (
            SELECT dc.customer_id, COALESCE(dc.customer_name, dc.customer_id) AS customer_name,
                   COALESCE(dc.customer_email, '') AS customer_email,
                   MAX(dd.full_date) AS last_purchase_date,
                   (MAX(MAX(dd.full_date)) OVER () - MAX(dd.full_date))::int AS recency_days,
                   COUNT(DISTINCT fs.transaction_id) AS frequency,
                   SUM(fs.revenue) AS monetary
            FROM fact_sales fs
            JOIN dim_date dd ON dd.date_key = fs.date_key
            JOIN dim_customer dc ON dc.customer_key = fs.customer_key
            GROUP BY dc.customer_id, dc.customer_name, dc.customer_email
        ), scored AS (
            SELECT *,
                   6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
                   NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
                   NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
            FROM customer_metrics
        )
        SELECT *,
               CASE WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
                    WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal customers'
                    WHEN r_score >= 4 AND f_score <= 2 THEN 'New customers'
                    WHEN r_score <= 2 AND f_score >= 3 THEN 'At risk'
                    WHEN r_score <= 2 THEN 'Hibernating'
                    ELSE 'Potential loyalists' END AS segment
        FROM scored
        ORDER BY monetary DESC
        """
    )


def store_codes() -> list[str]:
    frame = query_frame("SELECT store_code FROM dim_store ORDER BY store_code")
    return frame["store_code"].tolist() if not frame.empty else []


def _sales_filters(start_date: date | None, end_date: date | None, store_code: str | None) -> tuple[str, dict]:
    clauses: list[str] = []
    params: dict = {}
    if start_date:
        clauses.append("dd.full_date >= %(start_date)s")
        params["start_date"] = start_date
    if end_date:
        clauses.append("dd.full_date <= %(end_date)s")
        params["end_date"] = end_date
    if store_code and store_code != "All stores":
        clauses.append("ds.store_code = %(store_code)s")
        params["store_code"] = store_code
    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params
