from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

SALES_REQUIRED = {
    "transaction_id",
    "sale_date",
    "store_code",
    "product_sku",
    "quantity",
    "unit_price",
    "unit_cost",
}
INVENTORY_REQUIRED = {
    "snapshot_date",
    "store_code",
    "product_sku",
    "on_hand_qty",
    "reorder_point",
    "unit_cost",
}

STORE_DEFAULTS = {"store_name": "Unknown store", "city": "Unknown"}
PRODUCT_DEFAULTS = {
    "product_name": "Unknown product",
    "category": "Uncategorized",
    "brand": "Unbranded",
}


def read_csv(path: str | Path) -> pd.DataFrame:
    """Read a source CSV while preserving identifier values as text."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def records_to_frame(records: Iterable[dict]) -> pd.DataFrame:
    return pd.DataFrame(list(records))


def normalize_sales(source: pd.DataFrame) -> pd.DataFrame:
    """Validate and standardize sale lines before warehouse loading."""
    frame = source.copy()
    _require_columns(frame, SALES_REQUIRED, "sales")
    _add_defaults(frame, {**STORE_DEFAULTS, **PRODUCT_DEFAULTS})
    for column in ("customer_id", "customer_name", "customer_email"):
        if column not in frame:
            frame[column] = None

    _clean_identifiers(frame, ["transaction_id", "store_code", "product_sku", "customer_id"])
    _clean_text(frame, ["store_name", "city", "product_name", "category", "brand", "customer_name", "customer_email"])
    frame["sale_date"] = _parse_dates(frame["sale_date"], "sale_date")
    frame["quantity"] = _parse_numbers(frame["quantity"], "quantity", integer=True, positive=True)
    frame["unit_price"] = _parse_numbers(frame["unit_price"], "unit_price", positive=False)
    frame["unit_cost"] = _parse_numbers(frame["unit_cost"], "unit_cost", positive=False)
    _ensure_non_negative(frame, ["unit_price", "unit_cost"])
    _ensure_non_blank(frame, ["transaction_id", "store_code", "product_sku"])
    if frame["transaction_id"].duplicated().any():
        raise ValueError("sales contains duplicate transaction_id values")

    frame["revenue"] = (frame["quantity"] * frame["unit_price"]).round(2)
    frame["profit"] = (frame["revenue"] - frame["quantity"] * frame["unit_cost"]).round(2)
    return frame[
        [
            "transaction_id", "sale_date", "store_code", "store_name", "city", "product_sku",
            "product_name", "category", "brand", "customer_id", "customer_name", "customer_email",
            "quantity", "unit_price", "unit_cost", "revenue", "profit",
        ]
    ]


def normalize_inventory(source: pd.DataFrame) -> pd.DataFrame:
    """Validate and standardize inventory snapshots before warehouse loading."""
    frame = source.copy()
    _require_columns(frame, INVENTORY_REQUIRED, "inventory")
    _add_defaults(frame, {**STORE_DEFAULTS, **PRODUCT_DEFAULTS})
    _clean_identifiers(frame, ["store_code", "product_sku"])
    _clean_text(frame, ["store_name", "city", "product_name", "category", "brand"])
    frame["snapshot_date"] = _parse_dates(frame["snapshot_date"], "snapshot_date")
    frame["on_hand_qty"] = _parse_numbers(frame["on_hand_qty"], "on_hand_qty", integer=True, positive=False)
    frame["reorder_point"] = _parse_numbers(frame["reorder_point"], "reorder_point", integer=True, positive=False)
    frame["unit_cost"] = _parse_numbers(frame["unit_cost"], "unit_cost", positive=False)
    _ensure_non_negative(frame, ["on_hand_qty", "reorder_point", "unit_cost"])
    _ensure_non_blank(frame, ["store_code", "product_sku"])
    return frame[
        [
            "snapshot_date", "store_code", "store_name", "city", "product_sku", "product_name",
            "category", "brand", "on_hand_qty", "reorder_point", "unit_cost",
        ]
    ]


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def _add_defaults(frame: pd.DataFrame, defaults: dict[str, str]) -> None:
    for column, value in defaults.items():
        if column not in frame:
            frame[column] = value
        frame[column] = frame[column].replace("", value).fillna(value)


def _clean_identifiers(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column in frame:
            frame[column] = frame[column].replace("", None).where(frame[column].notna(), None)
            frame[column] = frame[column].map(lambda value: str(value).strip() if value is not None else None)


def _clean_text(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        frame[column] = frame[column].replace("", None).where(frame[column].notna(), None)
        frame[column] = frame[column].map(lambda value: str(value).strip() if value is not None else None)


def _parse_dates(values: pd.Series, column: str) -> pd.Series:
    parsed = pd.to_datetime(values, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{column} contains an invalid date")
    return parsed.dt.date


def _parse_numbers(values: pd.Series, column: str, *, integer: bool = False, positive: bool = False) -> pd.Series:
    parsed = pd.to_numeric(values, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{column} contains an invalid number")
    if integer and (parsed % 1 != 0).any():
        raise ValueError(f"{column} must contain whole numbers")
    if positive and (parsed <= 0).any():
        raise ValueError(f"{column} must be greater than zero")
    return parsed.astype(int) if integer else parsed.astype(float)


def _ensure_non_negative(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if (frame[column] < 0).any():
            raise ValueError(f"{column} cannot be negative")


def _ensure_non_blank(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if frame[column].isna().any() or (frame[column] == "").any():
            raise ValueError(f"{column} cannot be blank")
