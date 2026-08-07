"""Build the Global Superstore analytics lakehouse from its source CSV.

The output is a small, portable dimensional model.  Parquet remains the
source of truth; any query engine with Parquet support (DuckDB, Spark,
Polars,
Power BI, etc.) can read it directly.

Run from the repository root:
    python scripts/convert_csv_to_parquet.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = REPOSITORY_ROOT / "Global_Superstore2.csv"
DATASET_ROOT = REPOSITORY_ROOT / "data" / "global_superstore"

COLUMN_RENAMES = {
    "Row ID": "line_item_key",
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

DIM_DATE_SCHEMA = pa.schema(
    [
        pa.field("date_key", pa.int32(), nullable=False),
        pa.field("date", pa.date32(), nullable=False),
        pa.field("year", pa.int16(), nullable=False),
        pa.field("quarter", pa.int8(), nullable=False),
        pa.field("month", pa.int8(), nullable=False),
        pa.field("month_name", pa.string(), nullable=False),
        pa.field("year_month", pa.string(), nullable=False),
        pa.field("week_of_year", pa.int8(), nullable=False),
        pa.field("day_of_month", pa.int8(), nullable=False),
        pa.field("day_of_week", pa.int8(), nullable=False),
        pa.field("day_name", pa.string(), nullable=False),
        pa.field("is_weekend", pa.bool_(), nullable=False),
    ]
)

DIM_CUSTOMER_SCHEMA = pa.schema(
    [
        pa.field("customer_key", pa.string(), nullable=False),
        pa.field("customer_id", pa.string(), nullable=False),
        pa.field("customer_name", pa.string(), nullable=False),
        pa.field("segment", pa.string(), nullable=False),
    ]
)

DIM_PRODUCT_SCHEMA = pa.schema(
    [
        pa.field("product_key", pa.string(), nullable=False),
        pa.field("product_id", pa.string(), nullable=False),
        pa.field("category", pa.string(), nullable=False),
        pa.field("sub_category", pa.string(), nullable=False),
        pa.field("product_name", pa.string(), nullable=False),
    ]
)

DIM_GEOGRAPHY_SCHEMA = pa.schema(
    [
        pa.field("geography_key", pa.string(), nullable=False),
        pa.field("market", pa.string(), nullable=False),
        pa.field("region", pa.string(), nullable=False),
        pa.field("country", pa.string(), nullable=False),
        pa.field("state", pa.string(), nullable=False),
        pa.field("city", pa.string(), nullable=False),
        pa.field("postal_code", pa.string(), nullable=True),
    ]
)

DIM_SHIP_MODE_SCHEMA = pa.schema(
    [
        pa.field("ship_mode_key", pa.string(), nullable=False),
        pa.field("ship_mode", pa.string(), nullable=False),
    ]
)

DIM_ORDER_PRIORITY_SCHEMA = pa.schema(
    [
        pa.field("order_priority_key", pa.string(), nullable=False),
        pa.field("order_priority", pa.string(), nullable=False),
    ]
)

FACT_ORDER_SCHEMA = pa.schema(
    [
        pa.field("order_key", pa.string(), nullable=False),
        pa.field("order_id", pa.string(), nullable=False),
        pa.field("order_date_key", pa.int32(), nullable=False),
        pa.field("ship_date_key", pa.int32(), nullable=False),
        pa.field("customer_key", pa.string(), nullable=False),
        pa.field("geography_key", pa.string(), nullable=False),
        pa.field("ship_mode_key", pa.string(), nullable=False),
        pa.field("order_priority_key", pa.string(), nullable=False),
        pa.field("order_year", pa.int16(), nullable=False),
        pa.field("ship_days", pa.int16(), nullable=False),
    ]
)

FACT_ORDER_LINE_SCHEMA = pa.schema(
    [
        pa.field("line_item_key", pa.int32(), nullable=False),
        pa.field("order_key", pa.string(), nullable=False),
        pa.field("product_key", pa.string(), nullable=False),
        pa.field("order_year", pa.int16(), nullable=False),
        pa.field("sales", pa.float64(), nullable=False),
        pa.field("quantity", pa.int16(), nullable=False),
        pa.field("discount", pa.float64(), nullable=False),
        pa.field("profit", pa.float64(), nullable=False),
        pa.field("shipping_cost", pa.float64(), nullable=False),
    ]
)

MONTHLY_KPI_SCHEMA = pa.schema(
    [
        pa.field("month_start", pa.date32(), nullable=False),
        pa.field("order_year", pa.int16(), nullable=False),
        pa.field("order_month", pa.int8(), nullable=False),
        pa.field("line_items", pa.int64(), nullable=False),
        pa.field("orders", pa.int64(), nullable=False),
        pa.field("customers", pa.int64(), nullable=False),
        pa.field("sales", pa.float64(), nullable=False),
        pa.field("quantity", pa.int64(), nullable=False),
        pa.field("profit", pa.float64(), nullable=False),
        pa.field("profit_margin", pa.float64(), nullable=False),
        pa.field("shipping_cost", pa.float64(), nullable=False),
    ]
)

COUNTRY_KPI_SCHEMA = pa.schema(
    [
        pa.field("country", pa.string(), nullable=False),
        pa.field("line_items", pa.int64(), nullable=False),
        pa.field("orders", pa.int64(), nullable=False),
        pa.field("customers", pa.int64(), nullable=False),
        pa.field("sales", pa.float64(), nullable=False),
        pa.field("quantity", pa.int64(), nullable=False),
        pa.field("profit", pa.float64(), nullable=False),
        pa.field("profit_margin", pa.float64(), nullable=False),
        pa.field("shipping_cost", pa.float64(), nullable=False),
    ]
)


@dataclass(frozen=True)
class DatasetFile:
    """A physical Parquet file that is part of a logical dataset."""

    path: Path
    table: pa.Table


def stable_key(frame: pd.DataFrame, columns: list[str], prefix: str) -> pd.Series:
    """Create a deterministic, portable 64-bit hash key from business columns.

    A source ``Order ID`` and ``Product ID`` are not globally unique in this
    dataset.  Hashing the complete natural grain gives dimensions and facts a
    stable join key while preserving the source business ID as an attribute.
    Collisions are checked as part of model validation.
    """
    values = frame[columns].copy()
    for column in columns:
        if pd.api.types.is_datetime64_any_dtype(values[column]):
            values[column] = values[column].dt.strftime("%Y-%m-%d")
        values[column] = values[column].astype("string").fillna("<NULL>")
    canonical = values.agg("|".join, axis=1)
    return prefix + "_" + canonical.map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    )


def write_parquet(table: pa.Table, destination: Path) -> None:
    """Write an optimized Parquet file for analytical scans and joins."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table,
        destination,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
        row_group_size=10_000,
        version="2.6",
    )


def to_arrow_table(frame: pd.DataFrame, schema: pa.Schema) -> pa.Table:
    """Create a strictly typed Arrow table without a pandas index."""
    return pa.Table.from_pandas(frame, schema=schema, preserve_index=False, safe=True)


def date_key(series: pd.Series) -> pd.Series:
    return series.dt.strftime("%Y%m%d").astype("int32")


def load_source() -> pd.DataFrame:
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

    for column in ("line_item_key", "quantity"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    for column in ("sales", "discount", "profit", "shipping_cost"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    text_columns = [
        column
        for column in expected_columns
        if column
        not in {
            "line_item_key",
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

    if not frame["line_item_key"].is_unique:
        raise ValueError("line_item_key must be unique.")
    if (frame["ship_date"] < frame["order_date"]).any():
        raise ValueError("ship_date cannot precede order_date.")
    required_measures = ["sales", "quantity", "discount", "profit", "shipping_cost"]
    if frame[required_measures].isna().any(axis=None):
        raise ValueError("Required analytical measures cannot be null.")
    if (frame["quantity"] <= 0).any():
        raise ValueError("quantity must be greater than zero.")
    if (frame["sales"] < 0).any():
        raise ValueError("sales cannot be negative.")
    if ((frame["discount"] < 0) | (frame["discount"] > 1)).any():
        raise ValueError("discount must be between zero and one.")
    if (frame["shipping_cost"] < 0).any():
        raise ValueError("shipping_cost cannot be negative.")

    frame["order_year"] = frame["order_date"].dt.year.astype("int16")
    frame["order_month"] = frame["order_date"].dt.month.astype("int8")
    frame["ship_days"] = (frame["ship_date"] - frame["order_date"]).dt.days.astype("int16")
    return frame


def build_dimensions(fact: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build conformed dimensions with one row per business grain."""
    customer_columns = ["customer_id", "customer_name", "segment"]
    product_columns = ["product_id", "category", "sub_category", "product_name"]
    geography_columns = ["market", "region", "country", "state", "city", "postal_code"]

    fact["customer_key"] = stable_key(fact, ["customer_id"], "customer")
    fact["product_key"] = stable_key(fact, product_columns, "product")
    fact["geography_key"] = stable_key(fact, geography_columns, "geography")
    fact["ship_mode_key"] = stable_key(fact, ["ship_mode"], "ship_mode")
    fact["order_priority_key"] = stable_key(fact, ["order_priority"], "order_priority")

    order_columns = [
        "order_id",
        "order_date",
        "ship_date",
        "customer_key",
        "geography_key",
        "ship_mode_key",
        "order_priority_key",
    ]
    fact["order_key"] = stable_key(fact, order_columns, "order")

    date_range = pd.date_range(
        fact["order_date"].min(), fact["ship_date"].max(), freq="D"
    )
    dim_date = pd.DataFrame({"date": date_range})
    dim_date["date_key"] = date_key(dim_date["date"])
    dim_date["year"] = dim_date["date"].dt.year.astype("int16")
    dim_date["quarter"] = dim_date["date"].dt.quarter.astype("int8")
    dim_date["month"] = dim_date["date"].dt.month.astype("int8")
    dim_date["month_name"] = dim_date["date"].dt.month_name().astype("string")
    dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m").astype("string")
    dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype("int8")
    dim_date["day_of_month"] = dim_date["date"].dt.day.astype("int8")
    dim_date["day_of_week"] = dim_date["date"].dt.dayofweek.astype("int8")
    dim_date["day_name"] = dim_date["date"].dt.day_name().astype("string")
    dim_date["is_weekend"] = (dim_date["day_of_week"] >= 5)

    return {
        "dim_date": dim_date[list(DIM_DATE_SCHEMA.names)].sort_values("date_key"),
        "dim_customer": (
            fact[["customer_key", *customer_columns]]
            .drop_duplicates()
            .sort_values("customer_key")
        ),
        "dim_product": (
            fact[["product_key", *product_columns]]
            .drop_duplicates()
            .sort_values("product_key")
        ),
        "dim_geography": (
            fact[["geography_key", *geography_columns]]
            .drop_duplicates()
            .sort_values("geography_key")
        ),
        "dim_ship_mode": (
            fact[["ship_mode_key", "ship_mode"]].drop_duplicates().sort_values("ship_mode_key")
        ),
        "dim_order_priority": (
            fact[["order_priority_key", "order_priority"]]
            .drop_duplicates()
            .sort_values("order_priority_key")
        ),
    }


def build_facts(fact: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build header-level orders and line-level financial facts."""
    fact["order_date_key"] = date_key(fact["order_date"])
    fact["ship_date_key"] = date_key(fact["ship_date"])

    orders = fact[
        [
            "order_key",
            "order_id",
            "order_date_key",
            "ship_date_key",
            "customer_key",
            "geography_key",
            "ship_mode_key",
            "order_priority_key",
            "order_year",
            "ship_days",
        ]
    ].drop_duplicates()
    if not orders["order_key"].is_unique:
        raise ValueError("order_key must identify one order header.")

    lines = fact[
        [
            "line_item_key",
            "order_key",
            "product_key",
            "order_year",
            "sales",
            "quantity",
            "discount",
            "profit",
            "shipping_cost",
        ]
    ].copy()
    return {
        "fact_order": orders.sort_values("order_key"),
        "fact_order_line": lines.sort_values("line_item_key"),
    }


def build_marts(fact: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build compact dashboard aggregates from the conformed model."""
    monthly = (
        fact.groupby(["order_year", "order_month"], as_index=False, sort=True)
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
    monthly["order_month"] = monthly["order_month"].astype("int8")
    monthly["month_start"] = pd.to_datetime(
        {"year": monthly["order_year"], "month": monthly["order_month"], "day": 1}
    )
    monthly["profit_margin"] = monthly["profit"] / monthly["sales"]
    monthly = monthly[list(MONTHLY_KPI_SCHEMA.names)]

    country = (
        fact.groupby("country", as_index=False, sort=True)
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
    country["profit_margin"] = country["profit"] / country["sales"]
    return {
        "monthly_sales_kpis": monthly,
        "country_sales_kpis": country[list(COUNTRY_KPI_SCHEMA.names)],
    }


def assert_relationships(dimensions: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> None:
    """Fail the build if keys are duplicate, orphaned, or internally inconsistent."""
    primary_keys = {
        "dim_date": "date_key",
        "dim_customer": "customer_key",
        "dim_product": "product_key",
        "dim_geography": "geography_key",
        "dim_ship_mode": "ship_mode_key",
        "dim_order_priority": "order_priority_key",
        "fact_order": "order_key",
        "fact_order_line": "line_item_key",
    }
    for dataset, primary_key in primary_keys.items():
        table = facts.get(dataset, dimensions.get(dataset))
        if table[primary_key].isna().any() or not table[primary_key].is_unique:
            raise ValueError(f"{dataset}.{primary_key} must be non-null and unique.")

    relationships = [
        ("fact_order", "customer_key", "dim_customer", "customer_key"),
        ("fact_order", "geography_key", "dim_geography", "geography_key"),
        ("fact_order", "ship_mode_key", "dim_ship_mode", "ship_mode_key"),
        ("fact_order", "order_priority_key", "dim_order_priority", "order_priority_key"),
        ("fact_order", "order_date_key", "dim_date", "date_key"),
        ("fact_order", "ship_date_key", "dim_date", "date_key"),
        ("fact_order_line", "order_key", "fact_order", "order_key"),
        ("fact_order_line", "product_key", "dim_product", "product_key"),
    ]
    for child, foreign_key, parent, primary_key in relationships:
        parent_table = facts.get(parent, dimensions.get(parent))
        orphan_count = (~facts[child][foreign_key].isin(parent_table[primary_key])).sum()
        if orphan_count:
            raise ValueError(
                f"Referential integrity failed: {child}.{foreign_key} has {orphan_count} orphan(s)."
            )


def dataset_metadata(path: Path, table: pa.Table) -> dict[str, object]:
    return {
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "rows": table.num_rows,
        "columns": [
            {"name": field.name, "type": str(field.type), "nullable": field.nullable}
            for field in table.schema
        ],
        "size_bytes": path.stat().st_size,
        "compression": "zstd",
    }


def write_partitioned(
    frame: pd.DataFrame, schema: pa.Schema, destination: Path
) -> list[DatasetFile]:
    """Write one Parquet file per ``order_year`` Hive partition.

    ``order_year`` belongs to the directory name, not the physical file.  This
    avoids duplicating the partition value in every row and lets query engines
    prune complete directories before reading Parquet row groups.
    """
    files: list[DatasetFile] = []
    physical_schema = schema.remove(schema.get_field_index("order_year"))
    for year, partition in frame.groupby("order_year", sort=True):
        path = destination / f"order_year={year}" / "part-00000.parquet"
        table = to_arrow_table(partition[list(physical_schema.names)], physical_schema)
        write_parquet(table, path)
        files.append(DatasetFile(path, table))
    return files


def write_catalog(source: pd.DataFrame, files: list[DatasetFile]) -> None:
    """Publish machine-readable catalog and relationship contracts beside the data."""
    relationships = [
        {"from": "fact_order.customer_key", "to": "dim_customer.customer_key", "cardinality": "many-to-one"},
        {"from": "fact_order.geography_key", "to": "dim_geography.geography_key", "cardinality": "many-to-one"},
        {"from": "fact_order.ship_mode_key", "to": "dim_ship_mode.ship_mode_key", "cardinality": "many-to-one"},
        {"from": "fact_order.order_priority_key", "to": "dim_order_priority.order_priority_key", "cardinality": "many-to-one"},
        {"from": "fact_order.order_date_key", "to": "dim_date.date_key", "cardinality": "many-to-one", "role": "order date"},
        {"from": "fact_order.ship_date_key", "to": "dim_date.date_key", "cardinality": "many-to-one", "role": "ship date"},
        {"from": "fact_order_line.order_key", "to": "fact_order.order_key", "cardinality": "many-to-one"},
        {"from": "fact_order_line.product_key", "to": "dim_product.product_key", "cardinality": "many-to-one"},
    ]
    logical_schemas = {
        "dim_date": DIM_DATE_SCHEMA,
        "dim_customer": DIM_CUSTOMER_SCHEMA,
        "dim_product": DIM_PRODUCT_SCHEMA,
        "dim_geography": DIM_GEOGRAPHY_SCHEMA,
        "dim_ship_mode": DIM_SHIP_MODE_SCHEMA,
        "dim_order_priority": DIM_ORDER_PRIORITY_SCHEMA,
        "fact_order": FACT_ORDER_SCHEMA,
        "fact_order_line": FACT_ORDER_LINE_SCHEMA,
        "monthly_sales_kpis": MONTHLY_KPI_SCHEMA,
        "country_sales_kpis": COUNTRY_KPI_SCHEMA,
    }
    dataset_definitions = {
        "dim_date": ("dimensions", "dim_date.parquet", "one row per calendar date", "date_key"),
        "dim_customer": ("dimensions", "dim_customer.parquet", "one row per source customer", "customer_key"),
        "dim_product": ("dimensions", "dim_product.parquet", "one row per distinct product attribute combination", "product_key"),
        "dim_geography": ("dimensions", "dim_geography.parquet", "one row per market/region/country/state/city/postal-code combination", "geography_key"),
        "dim_ship_mode": ("dimensions", "dim_ship_mode.parquet", "one row per shipping mode", "ship_mode_key"),
        "dim_order_priority": ("dimensions", "dim_order_priority.parquet", "one row per order priority", "order_priority_key"),
        "fact_order": ("facts", "fact_order/order_year=*/part-*.parquet", "one row per distinct source order header", "order_key"),
        "fact_order_line": ("facts", "fact_order_line/order_year=*/part-*.parquet", "one row per source row / order line", "line_item_key"),
        "monthly_sales_kpis": ("marts", "monthly_sales_kpis.parquet", "one row per order month", None),
        "country_sales_kpis": ("marts", "country_sales_kpis.parquet", "one row per country", None),
    }
    logical_datasets = {}
    for name, (layer, relative_path, grain, primary_key) in dataset_definitions.items():
        logical_datasets[name] = {
            "layer": layer,
            "path": relative_path,
            "grain": grain,
            "schema": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in logical_schemas[name]
            ],
        }
        if primary_key:
            logical_datasets[name]["primary_key"] = primary_key
        if name in {"fact_order", "fact_order_line"}:
            logical_datasets[name]["partition_by"] = "order_year"
            logical_datasets[name]["partitioning"] = "Hive directory; the partition field is logical and is not repeated in the Parquet file"
    catalog = {
        "model_name": "global_superstore_analytics",
        "model_version": "2.0.0",
        "storage_format": "Parquet / Zstandard / dictionary encoding / statistics",
        "source": {
            "file": SOURCE_FILE.name,
            "encoding": "Windows-1252 (cp1252)",
            "date_format": "dd-mm-yyyy",
            "rows": len(source),
            "date_range": {
                "min_order_date": source["order_date"].min().date().isoformat(),
                "max_order_date": source["order_date"].max().date().isoformat(),
                "max_ship_date": source["ship_date"].max().date().isoformat(),
            },
        },
        "key_strategy": {
            "description": "Deterministic SHA-256 prefixes (64-bit hexadecimal) from the declared natural grain. The build validates uniqueness.",
            "reason": "The source Order ID and Product ID are not globally unique, so they are retained as business attributes rather than used as primary keys.",
        },
        "logical_datasets": logical_datasets,
        "relationships": relationships,
        "files": [dataset_metadata(item.path, item.table) for item in files],
    }
    output = DATASET_ROOT / "metadata" / "data_catalog.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    source = load_source()
    if DATASET_ROOT.exists():
        shutil.rmtree(DATASET_ROOT)

    dimensions = build_dimensions(source)
    facts = build_facts(source)
    marts = build_marts(source)
    assert_relationships(dimensions, facts)

    files: list[DatasetFile] = []
    schemas = {
        "dim_date": DIM_DATE_SCHEMA,
        "dim_customer": DIM_CUSTOMER_SCHEMA,
        "dim_product": DIM_PRODUCT_SCHEMA,
        "dim_geography": DIM_GEOGRAPHY_SCHEMA,
        "dim_ship_mode": DIM_SHIP_MODE_SCHEMA,
        "dim_order_priority": DIM_ORDER_PRIORITY_SCHEMA,
        "monthly_sales_kpis": MONTHLY_KPI_SCHEMA,
        "country_sales_kpis": COUNTRY_KPI_SCHEMA,
    }
    for name, frame in dimensions.items():
        path = DATASET_ROOT / "dimensions" / f"{name}.parquet"
        table = to_arrow_table(frame, schemas[name])
        write_parquet(table, path)
        files.append(DatasetFile(path, table))
    files.extend(
        write_partitioned(
            facts["fact_order"], FACT_ORDER_SCHEMA, DATASET_ROOT / "facts" / "fact_order"
        )
    )
    files.extend(
        write_partitioned(
            facts["fact_order_line"], FACT_ORDER_LINE_SCHEMA, DATASET_ROOT / "facts" / "fact_order_line"
        )
    )
    for name, frame in marts.items():
        path = DATASET_ROOT / "marts" / f"{name}.parquet"
        table = to_arrow_table(frame, schemas[name])
        write_parquet(table, path)
        files.append(DatasetFile(path, table))

    write_catalog(source, files)
    print(f"Built dimensional model from {len(source):,} source rows.")
    for file in files:
        print(f"- {file.path.relative_to(REPOSITORY_ROOT)}: {file.table.num_rows:,} rows")


if __name__ == "__main__":
    main()
