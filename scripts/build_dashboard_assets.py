"""Create lightweight JSON assets for the static GitHub Pages dashboards.

The source of truth remains the Parquet dimensional model. This script exports
only the aggregates needed by the browser so the public demo requires no API,
database, or in-browser Parquet engine.

Run after ``convert_csv_to_parquet.py``:
    python scripts/build_dashboard_assets.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = REPOSITORY_ROOT / "data" / "global_superstore"
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "assets" / "data" / "global-superstore.json"
SQL_SOURCE_PATH = REPOSITORY_ROOT / "sql" / "demo_analysis.sql"
SQL_OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "assets" / "sql" / "global-superstore.sql"


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
    for column in result.select_dtypes(include=["floating"]).columns:
        result[column] = result[column].round(2)
    return json.loads(result.to_json(orient="records"))


def percentage(numerator: float, denominator: float) -> float:
    """Return a rounded percentage while making divide-by-zero behavior explicit."""
    if denominator == 0:
        return 0.0
    return round(float(numerator / denominator * 100), 2)


def dashboard_slice(frame: pd.DataFrame, order_headers: pd.DataFrame) -> dict[str, object]:
    """Return the KPI and chart aggregates used by one dashboard filter state."""
    unique_orders = order_headers[order_headers["order_key"].isin(frame["order_key"])].drop_duplicates("order_key")
    monthly = (
        frame.groupby(["year_month", "year", "month"], as_index=False, sort=True)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"))
    )
    customer_value = (
        frame.groupby("customer_key", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"), orders=("order_key", "nunique"))
        .sort_values("sales", ascending=False)
    )
    product_value = (
        frame.groupby(["product_key", "product_name", "category"], as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"), orders=("order_key", "nunique"))
    )
    sales = float(frame["sales"].sum())
    profit = float(frame["profit"].sum())
    shipping_cost = float(frame["shipping_cost"].sum())
    order_count = int(unique_orders["order_key"].nunique())
    customer_count = int(unique_orders["customer_key"].nunique())
    top_customer_count = max(1, int(customer_count * 0.2 + 0.9999))
    repeat_customers = int((unique_orders.groupby("customer_key")["order_key"].nunique() > 1).sum())
    monthly_mean = float(monthly["sales"].mean())
    summary = {
        "sales": round(sales, 2),
        "profit": round(profit, 2),
        "orders": order_count,
        "customers": customer_count,
        "line_items": int(frame["line_item_key"].nunique()),
        "countries": int(frame["country"].nunique()),
        "profit_margin": percentage(profit, sales),
        "average_order_value": round(sales / order_count, 2),
        "profit_per_order": round(profit / order_count, 2),
        "sales_per_customer": round(sales / customer_count, 2),
        "shipping_cost_ratio": percentage(shipping_cost, sales),
        "average_discount": round(float(frame["discount"].mean() * 100), 2),
        "loss_making_line_share": percentage(int((frame["profit"] < 0).sum()), len(frame)),
        "loss_making_products": int((product_value["profit"] < 0).sum()),
        "loss_making_product_share": percentage(int((product_value["profit"] < 0).sum()), len(product_value)),
        "repeat_customer_rate": percentage(repeat_customers, customer_count),
        "top_20_customer_sales_share": percentage(customer_value.head(top_customer_count)["sales"].sum(), sales),
        "revenue_volatility_index": percentage(float(monthly["sales"].std(ddof=0)), monthly_mean),
    }
    categories = (
        frame.groupby("category", as_index=False, sort=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_key", "nunique"),
            shipping_cost=("shipping_cost", "sum"),
            avg_discount=("discount", "mean"),
        )
        .sort_values("sales", ascending=False)
    )
    categories["profit_margin"] = categories["profit"] / categories["sales"] * 100
    categories["avg_discount"] = categories["avg_discount"] * 100
    markets = (
        frame.groupby("market", as_index=False, sort=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_key", "nunique"),
            customers=("customer_key", "nunique"),
        )
        .sort_values("sales", ascending=False)
    )
    markets["profit_margin"] = markets["profit"] / markets["sales"] * 100
    countries = (
        frame.groupby("country", as_index=False, sort=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"), orders=("order_key", "nunique"))
        .sort_values("sales", ascending=False)
        .head(6)
    )
    countries["profit_margin"] = countries["profit"] / countries["sales"] * 100
    segments = (
        frame.groupby("segment", as_index=False, sort=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_key", "nunique"),
            customers=("customer_key", "nunique"),
        )
        .sort_values("sales", ascending=False)
    )
    segments["profit_margin"] = segments["profit"] / segments["sales"] * 100
    segments["average_order_value"] = segments["sales"] / segments["orders"]
    order_shipping = frame[["order_key", "ship_mode", "ship_days"]].drop_duplicates("order_key")
    shipping_speed = (
        order_shipping.groupby("ship_mode", as_index=False, sort=False)
        .agg(orders=("order_key", "nunique"), avg_ship_days=("ship_days", "mean"))
    )
    shipping_value = (
        frame.groupby("ship_mode", as_index=False, sort=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"), shipping_cost=("shipping_cost", "sum"))
    )
    shipping = shipping_speed.merge(shipping_value, on="ship_mode", validate="one_to_one")
    shipping["shipping_cost_ratio"] = shipping["shipping_cost"] / shipping["sales"] * 100
    shipping = shipping.sort_values("avg_ship_days")
    discount_frame = frame.assign(
        discount_band=pd.cut(
            frame["discount"],
            bins=[-0.001, 0, 0.1, 0.2, 0.3, float("inf")],
            labels=["0%", "0-10%", "10-20%", "20-30%", "Trên 30%"],
            include_lowest=True,
        )
    )
    discount_bands = (
        discount_frame.groupby("discount_band", observed=True, as_index=False)
        .agg(
            line_items=("line_item_key", "nunique"),
            sales=("sales", "sum"),
            profit=("profit", "sum"),
        )
    )
    discount_bands["profit_margin"] = discount_bands["profit"] / discount_bands["sales"] * 100
    loss_products = product_value.sort_values("profit").head(5)
    return {
        "summary": summary,
        "monthly": records(monthly, ["year_month", "year", "month", "sales", "profit"]),
        "categories": records(
            categories,
            ["category", "sales", "profit", "profit_margin", "orders", "shipping_cost", "avg_discount"],
        ),
        "markets": records(
            markets, ["market", "sales", "profit", "profit_margin", "orders", "customers"]
        ),
        "countries": records(
            countries, ["country", "sales", "profit", "profit_margin", "orders"]
        ),
        "segments": records(
            segments,
            ["segment", "sales", "profit", "profit_margin", "orders", "customers", "average_order_value"],
        ),
        "shipping": records(
            shipping,
            ["ship_mode", "orders", "avg_ship_days", "sales", "profit", "shipping_cost", "shipping_cost_ratio"],
        ),
        "discount_bands": records(
            discount_bands, ["discount_band", "line_items", "sales", "profit", "profit_margin"]
        ),
        "loss_products": records(
            loss_products, ["product_name", "category", "orders", "sales", "profit"]
        ),
    }


def main() -> None:
    project_metadata = json.loads(
        (MODEL_ROOT / "metadata" / "project.json").read_text(encoding="utf-8")
    )
    dates = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_date.parquet")
    customers = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_customer.parquet")
    geography = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_geography.parquet")
    products = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_product.parquet")
    ship_modes = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_ship_mode.parquet")
    order_priorities = pd.read_parquet(MODEL_ROOT / "dimensions" / "dim_order_priority.parquet")
    orders = read_partitioned(MODEL_ROOT / "facts" / "fact_order")
    lines = read_partitioned(MODEL_ROOT / "facts" / "fact_order_line")

    enriched = (
        lines.merge(orders, on="order_key", validate="many_to_one", suffixes=("", "_header"))
        .merge(
            products[["product_key", "product_name", "category", "sub_category"]],
            on="product_key",
            validate="many_to_one",
        )
        .merge(customers[["customer_key", "segment"]], on="customer_key", validate="many_to_one")
        .merge(
            geography[["geography_key", "market", "region", "country"]],
            on="geography_key",
            validate="many_to_one",
        )
        .merge(ship_modes, on="ship_mode_key", validate="many_to_one")
        .merge(
            dates[["date_key", "year", "quarter", "month", "year_month"]],
            left_on="order_date_key",
            right_on="date_key",
            validate="many_to_one",
        )
    )
    years = sorted(int(year) for year in orders["order_year"].unique())
    period_start = min(years)
    period_end = max(years)
    parquet_files = list(MODEL_ROOT.rglob("*.parquet"))
    quality = {
        "dimension_primary_keys_unique": bool(
            dates["date_key"].notna().all()
            and dates["date_key"].is_unique
            and customers["customer_key"].notna().all()
            and customers["customer_key"].is_unique
            and geography["geography_key"].notna().all()
            and geography["geography_key"].is_unique
            and products["product_key"].notna().all()
            and products["product_key"].is_unique
            and ship_modes["ship_mode_key"].notna().all()
            and ship_modes["ship_mode_key"].is_unique
            and order_priorities["order_priority_key"].notna().all()
            and order_priorities["order_priority_key"].is_unique
        ),
        "order_primary_key_unique": bool(orders["order_key"].notna().all() and orders["order_key"].is_unique),
        "line_primary_key_unique": bool(
            lines["line_item_key"].notna().all() and lines["line_item_key"].is_unique
        ),
        "orphan_order_keys": int((~lines["order_key"].isin(orders["order_key"])).sum()),
        "orphan_product_keys": int((~lines["product_key"].isin(products["product_key"])).sum()),
        "orphan_customer_keys": int((~orders["customer_key"].isin(customers["customer_key"])).sum()),
        "orphan_geography_keys": int((~orders["geography_key"].isin(geography["geography_key"])).sum()),
        "orphan_ship_mode_keys": int((~orders["ship_mode_key"].isin(ship_modes["ship_mode_key"])).sum()),
        "orphan_order_priority_keys": int(
            (~orders["order_priority_key"].isin(order_priorities["order_priority_key"])).sum()
        ),
        "orphan_order_date_keys": int((~orders["order_date_key"].isin(dates["date_key"])).sum()),
        "orphan_ship_date_keys": int((~orders["ship_date_key"].isin(dates["date_key"])).sum()),
        "null_measure_rows": int(
            lines[["sales", "quantity", "discount", "profit", "shipping_cost"]].isna().any(axis=1).sum()
        ),
        "invalid_quantity_rows": int((lines["quantity"] <= 0).sum()),
        "negative_sales_rows": int((lines["sales"] < 0).sum()),
        "negative_shipping_cost_rows": int((lines["shipping_cost"] < 0).sum()),
        "invalid_discount_rows": int(((lines["discount"] < 0) | (lines["discount"] > 1)).sum()),
        "ship_before_order_rows": int((orders["ship_date_key"] < orders["order_date_key"]).sum()),
    }
    all_dashboard = dashboard_slice(enriched, orders)
    year_dashboards = {
        str(year): dashboard_slice(enriched[enriched["year"] == year], orders)
        for year in years
    }
    first_summary = year_dashboards[str(period_start)]["summary"]
    latest_summary = year_dashboards[str(period_end)]["summary"]
    previous_summary = year_dashboards[str(years[-2])]["summary"]
    sales_growth = percentage(latest_summary["sales"] - previous_summary["sales"], previous_summary["sales"])
    profit_growth = percentage(
        latest_summary["profit"] - previous_summary["profit"], previous_summary["profit"]
    )
    analysis = {
        "latest_year": period_end,
        "comparison_year": years[-2],
        "sales_growth_pct": sales_growth,
        "profit_growth_pct": profit_growth,
        "revenue_profit_gap_pct": round(sales_growth - profit_growth, 2),
        "sales_cagr_pct": round(
            ((latest_summary["sales"] / first_summary["sales"]) ** (1 / (period_end - period_start)) - 1)
            * 100,
            2,
        ),
    }
    payload = {
        "project": {
            "id": project_metadata["id"],
            "name": project_metadata["name"],
            "period": f"{period_start}-{period_end}",
            "description": project_metadata["description"],
            "domain": project_metadata["domain"],
            "difficulty": project_metadata["difficulty"],
            "learning_path": project_metadata["learning_path"],
            "source_rows": int(len(lines)),
        },
        "model": {
            "table_count": 10,
            "parquet_files": len(parquet_files),
            "dimensions": 6,
            "facts": 2,
            "marts": 2,
            "fact_partitions": len(list((MODEL_ROOT / "facts").glob("*/order_year=*"))),
            "quality": quality,
        },
        "analysis": analysis,
        "filters": {"years": years},
        "dashboard": {
            "all": all_dashboard,
            "years": year_dashboards,
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SQL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SQL_SOURCE_PATH, SQL_OUTPUT_PATH)
    print(
        f"Wrote {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)} for {len(years)} dashboard filters "
        f"and synced {SQL_OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}."
    )


if __name__ == "__main__":
    main()
