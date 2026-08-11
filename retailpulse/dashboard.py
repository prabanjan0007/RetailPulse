from __future__ import annotations

from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RetailPulse",
    page_icon="🛍️",
    layout="wide",
)


# ============================================================
# DATA PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "sample"

SALES_FILE = DATA_DIR / "sales.csv"
INVENTORY_FILE = DATA_DIR / "inventory.csv"


# ============================================================
# HELPERS
# ============================================================

def money(value) -> str:
    try:
        return f"₹{float(value or 0):,.0f}"
    except Exception:
        return "₹0"


def number(value) -> str:
    try:
        return f"{float(value or 0):,.0f}"
    except Exception:
        return "0"


def load_data():
    """Load the existing CSV sample data."""

    if not SALES_FILE.exists():
        raise FileNotFoundError(
            f"Sales file not found:\n{SALES_FILE}"
        )

    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(
            f"Inventory file not found:\n{INVENTORY_FILE}"
        )

    sales = pd.read_csv(SALES_FILE)
    inventory = pd.read_csv(INVENTORY_FILE)

    # Dates
    sales["sale_date"] = pd.to_datetime(sales["sale_date"])
    inventory["snapshot_date"] = pd.to_datetime(
        inventory["snapshot_date"]
    )

    # Numeric fields
    numeric_sales = [
        "quantity",
        "unit_price",
        "unit_cost",
    ]

    for column in numeric_sales:
        sales[column] = pd.to_numeric(
            sales[column],
            errors="coerce",
        ).fillna(0)

    inventory_numeric = [
        "on_hand_qty",
        "reorder_point",
        "unit_cost",
    ]

    for column in inventory_numeric:
        inventory[column] = pd.to_numeric(
            inventory[column],
            errors="coerce",
        ).fillna(0)

    # Calculated sales fields
    sales["revenue"] = (
        sales["quantity"] * sales["unit_price"]
    )

    sales["cost"] = (
        sales["quantity"] * sales["unit_cost"]
    )

    sales["profit"] = (
        sales["revenue"] - sales["cost"]
    )

    sales["margin_pct"] = (
        sales["profit"]
        .div(sales["revenue"].replace(0, pd.NA))
        .fillna(0)
        * 100
    )

    # Inventory value
    inventory["inventory_value"] = (
        inventory["on_hand_qty"]
        * inventory["unit_cost"]
    )

    return sales, inventory


@st.cache_data(ttl=300)
def get_data():
    return load_data()


# ============================================================
# LOAD DATA
# ============================================================

try:
    sales, inventory = get_data()

except Exception as error:
    st.error("RetailPulse could not load the sample data.")
    st.code(str(error))
    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title("🛍️ RetailPulse")

st.caption(
    "Sales, profit, inventory health, and customer intelligence "
    "in one retail control room."
)

st.divider()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

with st.sidebar:

    st.header("🔎 Dashboard Filters")

    min_date = sales["sale_date"].min().date()
    max_date = sales["sale_date"].max().date()

    selected_range = st.date_input(
        "Sales period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    stores = [
        "All stores"
    ] + sorted(
        sales["store_code"].dropna().unique().tolist()
    )

    selected_store = st.selectbox(
        "Store",
        stores,
    )

    st.divider()

    st.info(
        "RetailPulse is currently running in "
        "**standalone sample-data mode**. "
        "PostgreSQL is not required."
    )


# ============================================================
# VALIDATE DATE RANGE
# ============================================================

if not isinstance(selected_range, tuple) or len(selected_range) != 2:
    st.warning("Please select both a start and end date.")
    st.stop()


start_date, end_date = selected_range


# ============================================================
# FILTER SALES
# ============================================================

filtered_sales = sales[
    (sales["sale_date"].dt.date >= start_date)
    & (sales["sale_date"].dt.date <= end_date)
].copy()


if selected_store != "All stores":
    filtered_sales = filtered_sales[
        filtered_sales["store_code"] == selected_store
    ]


# ============================================================
# CALCULATE OVERVIEW
# ============================================================

revenue = filtered_sales["revenue"].sum()
profit = filtered_sales["profit"].sum()

margin = (
    profit / revenue * 100
    if revenue
    else 0
)

transactions = filtered_sales["transaction_id"].nunique()

units = filtered_sales["quantity"].sum()


# ============================================================
# TABS
# ============================================================

overview_tab, inventory_tab, customers_tab, analysis_tab = st.tabs(
    [
        "📊 Sales Overview",
        "📦 Inventory & Alerts",
        "👥 Customers",
        "🔬 Products & Stores",
    ]
)


# ============================================================
# SALES OVERVIEW
# ============================================================

with overview_tab:

    st.subheader("Business Overview")

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric(
        "Revenue",
        money(revenue),
    )

    m2.metric(
        "Gross Profit",
        money(profit),
    )

    m3.metric(
        "Margin",
        f"{margin:.1f}%",
    )

    m4.metric(
        "Transactions",
        number(transactions),
    )

    m5.metric(
        "Units Sold",
        number(units),
    )

    st.divider()

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    st.subheader("📈 Sales & Profit Trend")

    if filtered_sales.empty:

        st.info(
            "No sales match the selected filters."
        )

    else:

        trend = (
            filtered_sales
            .groupby("sale_date", as_index=True)
            .agg(
                revenue=("revenue", "sum"),
                profit=("profit", "sum"),
            )
            .sort_index()
        )

        st.line_chart(
            trend,
            use_container_width=True,
        )

    st.divider()

    left, right = st.columns(2)

    # --------------------------------------------------------
    # TOP PRODUCTS
    # --------------------------------------------------------

    with left:

        st.subheader("🏆 Top Products by Revenue")

        if filtered_sales.empty:

            st.info("No product data.")

        else:

            products = (
                filtered_sales
                .groupby(
                    [
                        "product_name",
                        "category",
                    ],
                    as_index=False,
                )
                .agg(
                    revenue=("revenue", "sum"),
                    profit=("profit", "sum"),
                    units_sold=("quantity", "sum"),
                )
                .sort_values(
                    "revenue",
                    ascending=False,
                )
            )

            chart_products = (
                products
                .head(10)
                .set_index("product_name")[
                    ["revenue"]
                ]
            )

            st.bar_chart(
                chart_products,
                horizontal=True,
                use_container_width=True,
            )

    # --------------------------------------------------------
    # STORE REVENUE
    # --------------------------------------------------------

    with right:

        st.subheader("🏪 Store Revenue")

        if filtered_sales.empty:

            st.info("No store data.")

        else:

            store_summary = (
                filtered_sales
                .groupby(
                    [
                        "store_code",
                        "store_name",
                    ],
                    as_index=False,
                )
                .agg(
                    revenue=("revenue", "sum"),
                    profit=("profit", "sum"),
                    units_sold=("quantity", "sum"),
                    transactions=(
                        "transaction_id",
                        "nunique",
                    ),
                )
                .sort_values(
                    "revenue",
                    ascending=False,
                )
            )

            chart_stores = (
                store_summary
                .set_index("store_name")[
                    ["revenue"]
                ]
            )

            st.bar_chart(
                chart_stores,
                horizontal=True,
                use_container_width=True,
            )

    st.divider()

    st.subheader("📋 Sales Detail")

    if filtered_sales.empty:

        st.info("No transactions found.")

    else:

        display_sales = filtered_sales[
            [
                "transaction_id",
                "sale_date",
                "store_name",
                "product_name",
                "category",
                "customer_name",
                "quantity",
                "unit_price",
                "revenue",
                "profit",
                "margin_pct",
            ]
        ].copy()

        display_sales["sale_date"] = (
            display_sales["sale_date"]
            .dt.strftime("%Y-%m-%d")
        )

        st.dataframe(
            display_sales,
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# INVENTORY
# ============================================================

with inventory_tab:

    st.subheader("📦 Inventory Health")

    inventory_value = inventory[
        "inventory_value"
    ].sum()

    out_of_stock = int(
        (
            inventory["on_hand_qty"] == 0
        ).sum()
    )

    low_stock = int(
        (
            inventory["on_hand_qty"]
            <= inventory["reorder_point"]
        ).sum()
    )

    total_skus = len(inventory)

    a, b, c, d = st.columns(4)

    a.metric(
        "Inventory Value",
        money(inventory_value),
    )

    b.metric(
        "SKUs / Store",
        number(total_skus),
    )

    c.metric(
        "Low Stock",
        number(low_stock),
    )

    d.metric(
        "Out of Stock",
        number(out_of_stock),
    )

    st.divider()

    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    st.subheader("🚨 Replenishment Alerts")

    alerts = inventory[
        inventory["on_hand_qty"]
        <= inventory["reorder_point"]
    ].copy()

    if alerts.empty:

        st.success(
            "No products are currently below "
            "their reorder point."
        )

    else:

        alerts["severity"] = alerts.apply(
            lambda row:
                "Critical"
                if row["on_hand_qty"] == 0
                else (
                    "High"
                    if row["on_hand_qty"]
                    <= row["reorder_point"] / 2
                    else "Medium"
                ),
            axis=1,
        )

        alerts["suggested_order_qty"] = (
            alerts["reorder_point"]
            - alerts["on_hand_qty"]
        ).clip(lower=0)

        alerts["inventory_value"] = (
            alerts["on_hand_qty"]
            * alerts["unit_cost"]
        )

        alert_display = alerts[
            [
                "severity",
                "store_name",
                "product_name",
                "category",
                "on_hand_qty",
                "reorder_point",
                "suggested_order_qty",
                "inventory_value",
            ]
        ].copy()

        st.dataframe(
            alert_display,
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    # --------------------------------------------------------
    # INVENTORY CHART
    # --------------------------------------------------------

    st.subheader("📊 Inventory by Product")

    inventory_chart = (
        inventory
        .groupby(
            "product_name",
            as_index=True,
        )["on_hand_qty"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(
        inventory_chart,
        horizontal=True,
        use_container_width=True,
    )

    st.divider()

    st.subheader("📋 Latest Inventory Position")

    inventory_display = inventory.copy()

    inventory_display[
        "inventory_value"
    ] = inventory_display[
        "inventory_value"
    ].round(0)

    st.dataframe(
        inventory_display,
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# CUSTOMERS / RFM
# ============================================================

with customers_tab:

    st.subheader("👥 Customer Intelligence")

    if filtered_sales.empty:

        st.info("No customer data available.")

    else:

        customer = (
            filtered_sales
            .groupby(
                [
                    "customer_id",
                    "customer_name",
                    "customer_email",
                ],
                as_index=False,
            )
            .agg(
                last_purchase=(
                    "sale_date",
                    "max",
                ),
                frequency=(
                    "transaction_id",
                    "nunique",
                ),
                monetary=(
                    "revenue",
                    "sum",
                ),
                units=(
                    "quantity",
                    "sum",
                ),
            )
        )

        analysis_date = (
            filtered_sales["sale_date"].max()
        )

        customer["recency_days"] = (
            analysis_date
            - customer["last_purchase"]
        ).dt.days

        # RFM scores
        customer["R_score"] = pd.qcut(
            customer["recency_days"]
            .rank(method="first"),
            5,
            labels=[5, 4, 3, 2, 1],
        ).astype(int)

        customer["F_score"] = pd.qcut(
            customer["frequency"]
            .rank(method="first"),
            5,
            labels=[1, 2, 3, 4, 5],
        ).astype(int)

        customer["M_score"] = pd.qcut(
            customer["monetary"]
            .rank(method="first"),
            5,
            labels=[1, 2, 3, 4, 5],
        ).astype(int)

        def get_segment(row):

            r = row["R_score"]
            f = row["F_score"]
            m = row["M_score"]

            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"

            if r >= 3 and f >= 3:
                return "Loyal Customers"

            if r >= 4 and f <= 2:
                return "New Customers"

            if r <= 2 and f >= 3:
                return "At Risk"

            if r <= 2:
                return "Hibernating"

            return "Potential Loyalists"

        customer["segment"] = customer.apply(
            get_segment,
            axis=1,
        )

        # ----------------------------------------------------
        # CUSTOMER METRICS
        # ----------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Customers",
            number(len(customer)),
        )

        c2.metric(
            "Customer Revenue",
            money(customer["monetary"].sum()),
        )

        c3.metric(
            "Avg Customer Value",
            money(customer["monetary"].mean()),
        )

        c4.metric(
            "Repeat Customers",
            number(
                (
                    customer["frequency"] > 1
                ).sum()
            ),
        )

        st.divider()

        # ----------------------------------------------------
        # SEGMENTS
        # ----------------------------------------------------

        segment_summary = (
            customer
            .groupby(
                "segment",
                as_index=False,
            )
            .agg(
                customers=(
                    "customer_id",
                    "count",
                ),
                revenue=(
                    "monetary",
                    "sum",
                ),
            )
            .sort_values(
                "revenue",
                ascending=False,
            )
        )

        left, right = st.columns(2)

        with left:

            st.subheader(
                "Customer Segments"
            )

            segment_chart = (
                segment_summary
                .set_index("segment")[
                    ["customers"]
                ]
            )

            st.bar_chart(
                segment_chart,
                horizontal=True,
                use_container_width=True,
            )

        with right:

            st.subheader(
                "Segment Summary"
            )

            st.dataframe(
                segment_summary,
                hide_index=True,
                use_container_width=True,
            )

        st.divider()

        st.subheader(
            "📋 Customer RFM Analysis"
        )

        customer_display = customer[
            [
                "customer_id",
                "customer_name",
                "customer_email",
                "last_purchase",
                "recency_days",
                "frequency",
                "monetary",
                "R_score",
                "F_score",
                "M_score",
                "segment",
            ]
        ].sort_values(
            "monetary",
            ascending=False,
        )

        st.dataframe(
            customer_display,
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# PRODUCT & STORE ANALYSIS
# ============================================================

with analysis_tab:

    product_view, store_view = st.tabs(
        [
            "📦 Product Analysis",
            "🏪 Store Analysis",
        ]
    )

    # --------------------------------------------------------
    # PRODUCT ANALYSIS
    # --------------------------------------------------------

    with product_view:

        st.subheader(
            "📦 Product Performance"
        )

        if filtered_sales.empty:

            st.info("No product data.")

        else:

            product_analysis = (
                filtered_sales
                .groupby(
                    [
                        "product_sku",
                        "product_name",
                        "category",
                        "brand",
                    ],
                    as_index=False,
                )
                .agg(
                    units_sold=(
                        "quantity",
                        "sum",
                    ),
                    revenue=(
                        "revenue",
                        "sum",
                    ),
                    profit=(
                        "profit",
                        "sum",
                    ),
                )
            )

            product_analysis[
                "margin_pct"
            ] = (
                product_analysis["profit"]
                / product_analysis["revenue"]
                .replace(0, pd.NA)
                * 100
            ).fillna(0)

            product_analysis = (
                product_analysis
                .sort_values(
                    "revenue",
                    ascending=False,
                )
            )

            st.dataframe(
                product_analysis,
                hide_index=True,
                use_container_width=True,
            )

    # --------------------------------------------------------
    # STORE ANALYSIS
    # --------------------------------------------------------

    with store_view:

        st.subheader(
            "🏪 Store Performance"
        )

        if filtered_sales.empty:

            st.info("No store data.")

        else:

            store_analysis = (
                filtered_sales
                .groupby(
                    [
                        "store_code",
                        "store_name",
                        "city",
                    ],
                    as_index=False,
                )
                .agg(
                    revenue=(
                        "revenue",
                        "sum",
                    ),
                    profit=(
                        "profit",
                        "sum",
                    ),
                    units_sold=(
                        "quantity",
                        "sum",
                    ),
                    transactions=(
                        "transaction_id",
                        "nunique",
                    ),
                )
            )

            store_analysis[
                "margin_pct"
            ] = (
                store_analysis["profit"]
                / store_analysis["revenue"]
                .replace(0, pd.NA)
                * 100
            ).fillna(0)

            store_analysis = (
                store_analysis
                .sort_values(
                    "revenue",
                    ascending=False,
                )
            )

            st.dataframe(
                store_analysis,
                hide_index=True,
                use_container_width=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "RetailPulse • Standalone analytics mode • "
    "Powered by Streamlit + Pandas"
)