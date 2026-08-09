from __future__ import annotations

import argparse
from pathlib import Path

from retailpulse.db import initialize_schema
from retailpulse.ingest import normalize_inventory, normalize_sales, read_csv
from retailpulse.warehouse import load_inventory, load_sales


def load_files(sales_path: Path | None, inventory_path: Path | None) -> None:
    initialize_schema()
    if sales_path:
        loaded = load_sales(normalize_sales(read_csv(sales_path)))
        print(f"Loaded {loaded} sales records from {sales_path}")
    if inventory_path:
        loaded = load_inventory(normalize_inventory(read_csv(inventory_path)))
        print(f"Loaded {loaded} inventory records from {inventory_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="RetailPulse data loader")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Create or update the warehouse schema")
    samples = subparsers.add_parser("load-samples", help="Load included sales and inventory data")
    load = subparsers.add_parser("load", help="Load your own CSV files")
    load.add_argument("--sales", type=Path, help="Path to sales.csv")
    load.add_argument("--inventory", type=Path, help="Path to inventory.csv")

    args = parser.parse_args()
    if args.command == "init":
        initialize_schema()
        print("RetailPulse warehouse is ready")
    elif args.command == "load-samples":
        root = Path(__file__).parents[1] / "data" / "sample"
        load_files(root / "sales.csv", root / "inventory.csv")
    else:
        if not args.sales and not args.inventory:
            parser.error("Provide --sales, --inventory, or both")
        load_files(args.sales, args.inventory)


if __name__ == "__main__":
    main()
