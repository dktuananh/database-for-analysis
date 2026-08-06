"""Create lightweight JSON assets for the static GitHub Pages dashboards.

The source of truth remains the Parquet dimensional model. This script exports
only the aggregates needed by the browser so the public demo requires no API,
database, or in-browser Parquet engine.

Run after ``convert_csv_to_parquet.py``:
    python scripts/build_dashboard_assets.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = REPOSITORY_ROOT / "data" / "global_superstore"
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "assets" / "data" / "global-superstore.json"


def read_partitioned(directory: Path) -> pd.DataFrame:
    """Read Hive-partitioned facts and restore the physical partition field."""
    partitions = []
    for file in sorted(directory.glob("order_year=*/part-*.parquet")):
        frame = pd.read_parquet(file)
        frame["order_year"] = int(file.parent.name.split("=", maxsplit=1)[1])
        partitions.append(frame)
    if not partitions:
        raise FileNotFoundError(f"No Parquet partitions found under {directory}")
    return pd.concat(partitions, ignore_index=True)


def records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    """Round financial values and return JSON-compatible record dictionaries."""
    result = frame[columns].copy()
    for column in ("sales", "profit", "shipping_cost", "avg_ship_days"):
        if column in result:
            result[column] = result[column].round(2)
    return json.loads(result.to_json(orient="records"))


def dashboard_slice(frame: pd.DataFrame, order_headers: pd.DataFrame) -> dict[str, object]:
    """Return the KPI and chart aggregates used by one dashboard filter state."""
    unique_orders = order_headers[order_headers["order_key"].isin(frame["order_key"])]
    summary = {
        "sales": round(float(frame["sales"].sum()), 2),
        "profit": round(float(frame["profit"].sum()), 2),
        "orders": int(unique_orders["order_key"].nunique()),
        "customers": int(unique_orders["customer_key"].nunique()),
        "line_items": int(frame["line_item_key"].nunique()),
        "countries": int(frame["country"].nunique()),
        "profit_margin": round(float(frame["profit"].sum() / frame["sales"].sum() * 100), 2),
    }
    monthly = (
        frame.groupby(["year_month", "year", "month"], as_index=False, sort=True)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"))
    )
    categories = (
        frame.groupby("category", as_index=False, sort=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"))
        .sort_values("sales", ascending=False)
    )
    markets = (
        frame.groupby("market", as_index=False, sort=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"), orders=("order_key", "nunique"))
        .sort_values("sales", ascending=False)
    )
    countries = (
        frame.groupby("country", as_index=False, sort=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"), orders=("order_key", "nunique"))
        .sort_values("sales", ascending=False)
        .head(6)
    )
    order_shipping = frame[["order_key", "ship_mode", "ship_days"]].drop_duplicates("order_key")
    shipping = (
        order_shipping.groupby("ship_mode", as_index=False, sort=False)
        .agg(orders=("order_key", "nunique"), avg_ship_days=("ship_days", "mean"))
        .sort_values("avg_ship_days")
    )
    return {
        "summary": summary,
        "monthly": records(monthly, ["year_month", "year", "month", "sales", "profit"]),
        "categories": records(categories, ["category", "sales", "profit"]),
        "markets": records(markets, ["market", "sales", "profit", "orders"]),
        "countries": records(countries, ["country", "sales", "profit", "orders"]),
        "shipping": records(shipping, ["ship_mode", "orders", "avg_ship_days"]),
    }


def main() -> None:
    dates = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_date.parquet")
    geography = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_geography.parquet")
    products = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_product.parquet")
    ship_modes = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_ship_mode.parquet")
    orders = read_partitioned(MODEL_ROOT / "facts" / "fact_order")
    lines = read_partitioned(MODEL_ROOT / "facts" / "fact_order_line")

    enriched = (
        lines.merge(orders, on="order_key", validate="many_to_one", suffixes=("", "_header"))
        .merge(products[["product_key", "category"]], on="product_key", validate="many_to_one")
        .merge(geography[["geography_key", "market", "country"]], on="geography_key", validate="many_to_one")
        .merge(ship_modes, on="ship_mode_key", validate="many_to_one")
        .merge(
            dates[["date_key", "year", "month", "year_month"]],
            left_on="order_date_key",
            right_on="date_key",
            validate="many_to_one",
        )
    )
    years = sorted(int(year) for year in orders["order_year"].unique())
    period_start = min(years)
    period_end = max(years)
    payload = {
        "project": {
            "id": "global_superstore",
            "name": "Global Superstore",
            "period": f"{period_start}-{period_end}",
            "description": "Retail sales, profit and fulfilment analysis from a dimensional Parquet model.",
            "source_rows": int(len(lines)),
        },
        "filters": {"years": years},
        "dashboard": {
            "all": dashboard_slice(enriched, orders),
            "years": {
                str(year): dashboard_slice(enriched[enriched["year"] == year], orders)
                for year in years
            },
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)} for {len(years)} dashboard filters.")


if __name__ == "__main__":
    main()
