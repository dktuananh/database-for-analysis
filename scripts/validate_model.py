"""Validate the generated dimensional model and reconciliation marts.

Run from repository root after the build:
    python scripts/validate_model.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1] / "data" / "global_superstore"


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def read_partitioned(path: Path) -> pd.DataFrame:
    partitions = []
    for file in sorted(path.glob("order_year=*/part-*.parquet")):
        frame = read_parquet(file)
        frame["order_year"] = int(file.parent.name.split("=", maxsplit=1)[1])
        partitions.append(frame)
    if not partitions:
        raise FileNotFoundError(f"No partitions found under {path}")
    return pd.concat(partitions, ignore_index=True)


def assert_primary_key(frame: pd.DataFrame, name: str, key: str) -> None:
    if frame[key].isna().any() or not frame[key].is_unique:
        raise AssertionError(f"{name}.{key} must be non-null and unique")


def assert_foreign_key(
    child: pd.DataFrame, child_name: str, foreign_key: str, parent: pd.DataFrame, parent_name: str, primary_key: str
) -> None:
    orphan_count = (~child[foreign_key].isin(parent[primary_key])).sum()
    if orphan_count:
        raise AssertionError(
            f"{child_name}.{foreign_key} has {orphan_count} value(s) missing from {parent_name}.{primary_key}"
        )


def main() -> None:
    dimensions = {
        "dim_date": read_parquet(ROOT / "dimensions" / "dim_date.parquet"),
        "dim_customer": read_parquet(ROOT / "dimensions" / "dim_customer.parquet"),
        "dim_product": read_parquet(ROOT / "dimensions" / "dim_product.parquet"),
        "dim_geography": read_parquet(ROOT / "dimensions" / "dim_geography.parquet"),
        "dim_ship_mode": read_parquet(ROOT / "dimensions" / "dim_ship_mode.parquet"),
        "dim_order_priority": read_parquet(ROOT / "dimensions" / "dim_order_priority.parquet"),
    }
    orders = read_partitioned(ROOT / "facts" / "fact_order")
    lines = read_partitioned(ROOT / "facts" / "fact_order_line")
    monthly = read_parquet(ROOT / "marts" / "monthly_sales_kpis.parquet")
    country = read_parquet(ROOT / "marts" / "country_sales_kpis.parquet")

    for name, key in {
        "dim_date": "date_key",
        "dim_customer": "customer_key",
        "dim_product": "product_key",
        "dim_geography": "geography_key",
        "dim_ship_mode": "ship_mode_key",
        "dim_order_priority": "order_priority_key",
    }.items():
        assert_primary_key(dimensions[name], name, key)
    assert_primary_key(orders, "fact_order", "order_key")
    assert_primary_key(lines, "fact_order_line", "line_item_key")

    for foreign_key, parent_name, primary_key in [
        ("customer_key", "dim_customer", "customer_key"),
        ("geography_key", "dim_geography", "geography_key"),
        ("ship_mode_key", "dim_ship_mode", "ship_mode_key"),
        ("order_priority_key", "dim_order_priority", "order_priority_key"),
        ("order_date_key", "dim_date", "date_key"),
        ("ship_date_key", "dim_date", "date_key"),
    ]:
        assert_foreign_key(orders, "fact_order", foreign_key, dimensions[parent_name], parent_name, primary_key)
    assert_foreign_key(lines, "fact_order_line", "order_key", orders, "fact_order", "order_key")
    assert_foreign_key(lines, "fact_order_line", "product_key", dimensions["dim_product"], "dim_product", "product_key")

    required_measures = ["sales", "quantity", "discount", "profit", "shipping_cost"]
    if lines[required_measures].isna().any(axis=None):
        raise AssertionError("fact_order_line contains null analytical measures")
    if (lines["quantity"] <= 0).any():
        raise AssertionError("fact_order_line.quantity must be greater than zero")
    if (lines["sales"] < 0).any():
        raise AssertionError("fact_order_line.sales cannot be negative")
    if ((lines["discount"] < 0) | (lines["discount"] > 1)).any():
        raise AssertionError("fact_order_line.discount must be between zero and one")
    if (lines["shipping_cost"] < 0).any():
        raise AssertionError("fact_order_line.shipping_cost cannot be negative")
    if (orders["ship_days"] < 0).any():
        raise AssertionError("fact_order.ship_days cannot be negative")

    enriched = (
        lines.merge(orders[["order_key", "order_date_key", "customer_key", "geography_key"]], on="order_key")
        .merge(dimensions["dim_date"][["date_key", "year", "month"]], left_on="order_date_key", right_on="date_key")
    )
    expected_monthly = (
        enriched.groupby(["year", "month"], as_index=False)
        .agg(
            line_items=("line_item_key", "count"),
            orders=("order_key", "nunique"),
            customers=("customer_key", "nunique"),
            sales=("sales", "sum"),
            quantity=("quantity", "sum"),
            profit=("profit", "sum"),
            shipping_cost=("shipping_cost", "sum"),
        )
        .rename(columns={"year": "order_year", "month": "order_month"})
    )
    expected_monthly["profit_margin"] = expected_monthly["profit"] / expected_monthly["sales"]
    observed_monthly = monthly.drop(columns="month_start")
    pd.testing.assert_frame_equal(
        observed_monthly.sort_values(["order_year", "order_month"]).reset_index(drop=True),
        expected_monthly[observed_monthly.columns]
        .sort_values(["order_year", "order_month"])
        .reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-10,
        atol=1e-10,
    )

    expected_country = (
        enriched.merge(dimensions["dim_geography"][["geography_key", "country"]], on="geography_key")
        .groupby("country", as_index=False)
        .agg(
            line_items=("line_item_key", "count"),
            orders=("order_key", "nunique"),
            customers=("customer_key", "nunique"),
            sales=("sales", "sum"),
            quantity=("quantity", "sum"),
            profit=("profit", "sum"),
            shipping_cost=("shipping_cost", "sum"),
        )
    )
    expected_country["profit_margin"] = expected_country["profit"] / expected_country["sales"]
    pd.testing.assert_frame_equal(
        country.sort_values("country").reset_index(drop=True),
        expected_country[country.columns].sort_values("country").reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-10,
        atol=1e-10,
    )

    print(
        "Validation passed: key, relationship, domain, temporal and mart checks; "
        f"{len(lines):,} line items, {len(orders):,} orders, "
        f"{len(dimensions['dim_customer']):,} customers, {len(dimensions['dim_product']):,} products."
    )


if __name__ == "__main__":
    main()
