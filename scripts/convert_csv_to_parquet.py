"""Convert the Global Superstore CSV into dashboard-ready Parquet datasets.

Run from the repository root:
    python scripts/convert_csv_to_parquet.py

The source CSV uses Windows-1252 encoding and dd-mm-yyyy dates.  The output
uses snake_case column names, typed date/numeric fields, and Zstandard
compression.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = REPOSITORY_ROOT / "Global_Superstore2.csv"
OUTPUT_DIRECTORY = REPOSITORY_ROOT / "data"

COLUMN_RENAMES = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "City": "city",
    "State": "state",
    "Country": "country",
    "Postal Code": "postal_code",
    "Market": "market",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
    "Shipping Cost": "shipping_cost",
    "Order Priority": "order_priority",
}

FACT_SCHEMA = pa.schema(
    [
        pa.field("row_id", pa.int32()),
        pa.field("order_id", pa.string()),
        pa.field("order_date", pa.date32()),
        pa.field("ship_date", pa.date32()),
        pa.field("ship_mode", pa.string()),
        pa.field("customer_id", pa.string()),
        pa.field("customer_name", pa.string()),
        pa.field("segment", pa.string()),
        pa.field("city", pa.string()),
        pa.field("state", pa.string()),
        pa.field("country", pa.string()),
        pa.field("postal_code", pa.string()),
        pa.field("market", pa.string()),
        pa.field("region", pa.string()),
        pa.field("product_id", pa.string()),
        pa.field("category", pa.string()),
        pa.field("sub_category", pa.string()),
        pa.field("product_name", pa.string()),
        pa.field("sales", pa.float64()),
        pa.field("quantity", pa.int16()),
        pa.field("discount", pa.float64()),
        pa.field("profit", pa.float64()),
        pa.field("shipping_cost", pa.float64()),
        pa.field("order_priority", pa.string()),
        pa.field("order_year", pa.int16()),
        pa.field("order_month", pa.int8()),
        pa.field("ship_days", pa.int16()),
    ]
)


def write_parquet(table: pa.Table, destination: Path) -> None:
    """Write an optimized Parquet file with metadata for column pruning."""
    pq.write_table(
        table,
        destination,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
        row_group_size=10_000,
        version="2.6",
    )


def to_arrow_table(frame: pd.DataFrame, schema: pa.Schema | None = None) -> pa.Table:
    """Create an Arrow table without retaining a pandas index."""
    return pa.Table.from_pandas(frame, schema=schema, preserve_index=False, safe=True)


def build_fact_table() -> pd.DataFrame:
    """Load, validate, type, and enrich the source transactions."""
    if not SOURCE_FILE.is_file():
        raise FileNotFoundError(f"Source CSV was not found: {SOURCE_FILE}")

    frame = pd.read_csv(
        SOURCE_FILE,
        encoding="cp1252",
        dtype={"Postal Code": "string"},
        low_memory=False,
    ).rename(columns=COLUMN_RENAMES)

    expected_columns = list(COLUMN_RENAMES.values())
    if list(frame.columns) != expected_columns:
        raise ValueError("The source CSV columns do not match the expected Global Superstore schema.")

    frame["order_date"] = pd.to_datetime(frame["order_date"], format="%d-%m-%Y", errors="raise")
    frame["ship_date"] = pd.to_datetime(frame["ship_date"], format="%d-%m-%Y", errors="raise")

    for column in ("row_id", "quantity"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    for column in ("sales", "discount", "profit", "shipping_cost"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    text_columns = [
        column
        for column in expected_columns
        if column
        not in {
            "row_id",
            "order_date",
            "ship_date",
            "sales",
            "quantity",
            "discount",
            "profit",
            "shipping_cost",
        }
    ]
    for column in text_columns:
        frame[column] = frame[column].astype("string")

    frame["order_year"] = frame["order_date"].dt.year.astype("int16")
    frame["order_month"] = frame["order_date"].dt.month.astype("int8")
    frame["ship_days"] = (frame["ship_date"] - frame["order_date"]).dt.days.astype("int16")

    if not frame["row_id"].is_unique:
        raise ValueError("row_id must be unique.")
    if (frame["ship_days"] < 0).any():
        raise ValueError("ship_date cannot precede order_date.")

    return frame[list(FACT_SCHEMA.names)]


def build_monthly_kpis(fact: pd.DataFrame) -> pd.DataFrame:
    """Create a compact monthly KPI dataset for fast dashboard overview charts."""
    monthly = (
        fact.groupby(["order_year", "order_month"], as_index=False, sort=True)
        .agg(
            line_items=("row_id", "count"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            sales=("sales", "sum"),
            quantity=("quantity", "sum"),
            profit=("profit", "sum"),
            shipping_cost=("shipping_cost", "sum"),
        )
    )
    monthly["month_start"] = pd.to_datetime(
        {"year": monthly["order_year"], "month": monthly["order_month"], "day": 1}
    )
    monthly["profit_margin"] = monthly["profit"] / monthly["sales"]
    return monthly[
        [
            "month_start",
            "order_year",
            "order_month",
            "line_items",
            "orders",
            "customers",
            "sales",
            "quantity",
            "profit",
            "profit_margin",
            "shipping_cost",
        ]
    ]


def build_country_kpis(fact: pd.DataFrame) -> pd.DataFrame:
    """Create country-level KPI data for maps and geographic ranking views."""
    country = (
        fact.groupby(["country"], as_index=False, sort=True)
        .agg(
            line_items=("row_id", "count"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            sales=("sales", "sum"),
            quantity=("quantity", "sum"),
            profit=("profit", "sum"),
            shipping_cost=("shipping_cost", "sum"),
        )
    )
    country["profit_margin"] = country["profit"] / country["sales"]
    return country[
        [
            "country",
            "line_items",
            "orders",
            "customers",
            "sales",
            "quantity",
            "profit",
            "profit_margin",
            "shipping_cost",
        ]
    ]


def file_metadata(path: Path, table: pa.Table) -> dict[str, object]:
    return {
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "rows": table.num_rows,
        "columns": table.column_names,
        "size_bytes": path.stat().st_size,
    }


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)

    fact = build_fact_table()
    monthly = build_monthly_kpis(fact)
    country = build_country_kpis(fact)

    output_tables = {
        OUTPUT_DIRECTORY / "fact_sales.parquet": to_arrow_table(fact, FACT_SCHEMA),
        OUTPUT_DIRECTORY / "monthly_kpis.parquet": to_arrow_table(monthly),
        OUTPUT_DIRECTORY / "country_kpis.parquet": to_arrow_table(country),
    }
    for path, table in output_tables.items():
        write_parquet(table, path)

    manifest = {
        "source": {
            "file": SOURCE_FILE.name,
            "encoding": "Windows-1252 (cp1252)",
            "date_format": "dd-mm-yyyy",
            "rows": len(fact),
            "date_range": {
                "min": fact["order_date"].min().date().isoformat(),
                "max": fact["order_date"].max().date().isoformat(),
            },
        },
        "datasets": [file_metadata(path, table) for path, table in output_tables.items()],
        "fact_schema": [
            {"name": field.name, "type": str(field.type), "nullable": field.nullable}
            for field in FACT_SCHEMA
        ],
    }
    (OUTPUT_DIRECTORY / "dataset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Converted {len(fact):,} source rows into {len(output_tables)} Parquet datasets.")
    for path, table in output_tables.items():
        print(f"- {path.relative_to(REPOSITORY_ROOT)}: {table.num_rows:,} rows, {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
