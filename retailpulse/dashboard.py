from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from retailpulse import analytics

st.set_page_config(page_title="RetailPulse", page_icon="🛍️", layout="wide")


def money(value: float) -> str:
    return f"₹{float(value or 0):,.0f}"


def number(value: float) -> str:
    return f"{float(value or 0):,.0f}"


@st.cache_data(ttl=45, show_spinner=False)
def load_overview(start: date, end: date, store: str):
    return (
        analytics.sales_summary(start, end, store),
        analytics.sales_trend(start, end, store),
        analytics.product_performance(start, end, store),
        analytics.store_performance(start, end),
    )


@st.cache_data(ttl=45, show_spinner=False)
def load_inventory():
    return analytics.inventory_overview(), analytics.low_stock_alerts()


@st.cache_data(ttl=45, show_spinner=False)
def load_rfm():
    return analytics.rfm_segments()


def app() -> None:
    st.title("RetailPulse")
    st.caption("Sales, profit, inventory health, and customer intelligence in one retail control room.")

    try:
        bounds = analytics.query_frame("SELECT MIN(full_date) AS min_date, MAX(full_date) AS max_date FROM dim_date")
        if bounds.empty or bounds.iloc[0]["min_date"] is None:
            st.info("No data loaded yet. Run `python -m retailpulse.cli load-samples` to explore the dashboard.")
            return
        min_date, max_date = bounds.iloc[0]["min_date"], bounds.iloc[0]["max_date"]
        stores = ["All stores", *analytics.store_codes()]
    except Exception as error:
        st.error("RetailPulse cannot reach PostgreSQL. Start the database with `docker compose up -d`.")
        st.caption(str(error))
        return

    with st.sidebar:
        st.header("Filters")
        selected_range = st.date_input("Sales period", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        selected_store = st.selectbox("Store", stores)
        st.divider()
        st.caption("Inventory alerts always use the latest inventory snapshot and the last 30 days of sales velocity.")

    if not isinstance(selected_range, tuple) or len(selected_range) != 2:
        st.warning("Select both a start and end date to view the dashboard.")
        return
    start_date, end_date = selected_range
    summary, trend, products, stores_data = load_overview(start_date, end_date, selected_store)
    inventory, alerts = load_inventory()
    rfm = load_rfm()

    overview_tab, inventory_tab, customers_tab, analysis_tab = st.tabs(
        ["Sales overview", "Inventory & alerts", "Customers", "Products & stores"]
    )

    with overview_tab:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Revenue", money(summary["revenue"]))
        m2.metric("Gross profit", money(summary["profit"]))
        m3.metric("Margin", f"{float(summary['margin_pct'] or 0):.1f}%")
        m4.metric("Transactions", number(summary["transactions"]))
        m5.metric("Units sold", number(summary["units"]))

        st.subheader("Sales and profit trend")
        if trend.empty:
            st.info("No sales match the selected filters.")
        else:
            chart = trend.set_index("date")[["revenue", "profit"]]
            st.line_chart(chart, use_container_width=True)

        left, right = st.columns(2)
        with left:
            st.subheader("Top products by revenue")
            if not products.empty:
                top_products = products.head(10).set_index("product_name")[["revenue"]]
                st.bar_chart(top_products, horizontal=True, use_container_width=True)
        with right:
            st.subheader("Store revenue")
            if not stores_data.empty:
                st.bar_chart(stores_data.set_index("store_name")[["revenue"]], horizontal=True, use_container_width=True)

    with inventory_tab:
        inventory_value = inventory["inventory_value"].sum() if not inventory.empty else 0
        out_of_stock = int((inventory["on_hand_qty"] == 0).sum()) if not inventory.empty else 0
        a, b, c = st.columns(3)
        a.metric("Inventory value", money(inventory_value))
        b.metric("Active SKUs / stores", number(len(inventory)))
        c.metric("Out of stock", number(out_of_stock), delta="Needs attention" if out_of_stock else "Healthy", delta_color="inverse")
        st.subheader("Low-stock alert queue")
        if alerts.empty:
            st.success("No products are currently below their reorder point.")
        else:
            st.error(f"{len(alerts)} replenishment alerts need review.")
            st.dataframe(
                alerts,
                column_config={
                    "suggested_order_qty": st.column_config.NumberColumn("Suggested order", format="%d units"),
                    "avg_daily_units": st.column_config.NumberColumn("Avg daily sales", format="%.2f"),
                    "days_of_cover": st.column_config.NumberColumn("Days of cover", format="%.1f"),
                },
                hide_index=True,
                use_container_width=True,
            )
        st.subheader("Latest inventory position")
        if not inventory.empty:
            st.dataframe(inventory, hide_index=True, use_container_width=True)

    with customers_tab:
        st.subheader("RFM customer segments")
        if rfm.empty:
            st.info("Customer IDs are required on sales records to calculate RFM segments.")
        else:
            segment_summary = rfm.groupby("segment", as_index=False).agg(
                customers=("customer_id", "count"), revenue=("monetary", "sum")
            ).sort_values("revenue", ascending=False)
            left, right = st.columns([1, 2])
            with left:
                st.bar_chart(segment_summary.set_index("segment")[["customers"]], horizontal=True, use_container_width=True)
            with right:
                st.dataframe(segment_summary, hide_index=True, use_container_width=True)
            st.caption("RFM ranks customers by recency, purchase frequency, and total spend. Use ‘At risk’ and ‘Hibernating’ lists for win-back campaigns.")
            st.dataframe(rfm, hide_index=True, use_container_width=True)

    with analysis_tab:
        product_view, store_view = st.tabs(["Product analysis", "Store analysis"])
        with product_view:
            st.dataframe(products, hide_index=True, use_container_width=True)
        with store_view:
            st.dataframe(stores_data, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    app()
