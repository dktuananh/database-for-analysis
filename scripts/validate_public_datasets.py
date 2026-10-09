"""Validate saved Parquet, source pins, domain rules and mart reconciliation.

python scripts/validate_public_datasets.py
python scripts/validate_public_datasets.py --verify-source  # slower: compare every source value
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from pandas.testing import assert_frame_equal

from public_dataset_specs import COLUMNS, SOURCES, TARGETS

ROOT = Path(__file__).resolve().parents[1]


def validate_frames(project_id, frames, mart_name, mart):
    checks = []
    source = SOURCES[project_id]

    def check(name, passed, details=None):
        if not bool(passed):
            raise ValueError(f"{project_id}: {name} failed: {details}")
        checks.append({"name": name, "status": "passed", "details": details})

    def domain(frame, column, minimum, maximum):
        check(f"{column} in [{minimum}, {maximum}]", frame[column].between(minimum, maximum).all())

    primary = frames[source["primary_table"]]
    check("source snapshot row count", len(primary) == source["expected_rows"], len(primary))
    profiles = {}
    for name, frame in frames.items():
        expected = set(COLUMNS[project_id]) | {"record_id", "source_file", "source_row"}
        if project_id == "bike_sharing" and name == "daily_rentals":
            expected -= {"hour", "timestamp"}
        check(f"{name}: exact column contract", set(frame) == expected, list(frame))
        check(f"{name}: non-null unique snapshot keys", frame["record_id"].notna().all() and frame["record_id"].is_unique)
        check(f"{name}: source row provenance unique", not frame.duplicated(["source_file", "source_row"]).any())
        for filename, part in frame.groupby("source_file", sort=False):
            check(f"{name}: contiguous source rows {filename}",
                  part["source_row"].tolist() == list(range(1, len(part) + 1)))
            expected_ids = [f"{Path(filename).stem}:{i:06d}" for i in part["source_row"]]
            check(f"{name}: key maps to source {filename}", part["record_id"].tolist() == expected_ids)
        allowed_nulls = {"description", "customer_id"} if project_id == "online_retail" else set()
        required = [column for column in frame if column not in allowed_nulls]
        check(f"{name}: required values present", not frame[required].isna().any().any())
        numeric = frame.select_dtypes(include="number")
        check(f"{name}: finite numeric values", all(numeric[column].map(math.isfinite).all() for column in numeric))
        values = frame.drop(columns=["record_id", "source_file", "source_row"])
        profiles[name] = {
            "rows": len(frame), "columns": len(frame.columns),
            "null_counts": {column: int(count) for column, count in frame.isna().sum().items()},
            "duplicate_value_rows_after_first": int(values.duplicated().sum()),
            "duplicate_policy": "preserved; excludes record_id/source_file/source_row from comparison",
        }
        profiles[name]["numeric_ranges"] = {
            column: {"min": float(frame[column].min()), "max": float(frame[column].max())}
            for column in numeric if column != "source_row"
        }
        for target in TARGETS.get(project_id, []):
            profiles[name].setdefault("target_summary", {})[target] = {
                "non_null": int(frame[target].notna().sum()), "distinct": int(frame[target].nunique())}

    observations = {}
    if project_id == "online_retail":
        check("line amount = quantity x unit price", primary["line_amount_gbp"].eq(primary["quantity"] * primary["unit_price_gbp"]).all())
        check("cancellation flag from invoice prefix", primary["is_cancellation"].eq(primary["invoice_no"].str.upper().str.startswith("C")).all())
        check("invoice dates cover known snapshot", primary["invoice_date"].min().date().isoformat() == "2010-12-01"
              and primary["invoice_date"].max().date().isoformat() == "2011-12-09")
        observations = {"cancellation_lines": int(primary["is_cancellation"].sum()),
            "nonpositive_quantity_lines": int(primary["quantity"].le(0).sum()),
            "nonpositive_unit_price_lines": int(primary["unit_price_gbp"].le(0).sum()),
            "policy": "All source observations retained; no imputation or deduplication"}
    elif project_id == "bike_sharing":
        check("official daily row count", len(frames["daily_rentals"]) == 731)
        for name, frame in frames.items():
            check(f"{name}: component counts reconcile", frame["rental_count"].eq(frame["casual_count"] + frame["registered_count"]).all())
            for column in ["rental_count", "casual_count", "registered_count"]:
                check(f"{name}: {column} nonnegative", frame[column].ge(0).all())
            for column in ["temperature_normalized", "feels_like_normalized", "humidity_normalized", "windspeed_normalized"]:
                domain(frame, column, 0, 1)
            domain(frame, "season", 1, 4)
            domain(frame, "weather_situation", 1, 4)
            domain(frame, "weekday", 0, 6)
            for column in ["holiday", "working_day", "year_code"]:
                domain(frame, column, 0, 1)
            domain(frame, "month", 1, 12)
            check(f"{name}: year/date consistent", frame["year_code"].eq(frame["date"].dt.year - 2011).all())
            check(f"{name}: month/date consistent", frame["month"].eq(frame["date"].dt.month).all())
            check(f"{name}: weekday/date consistent", frame["weekday"].eq((frame["date"].dt.dayofweek + 1) % 7).all())
            check(f"{name}: working day consistent", frame["working_day"].eq(
                (~frame["weekday"].isin([0, 6]) & frame["holiday"].eq(0)).astype("int64")).all())
        domain(primary, "hour", 0, 23)
        check("hour timestamp derived correctly", primary["timestamp"].eq(primary["date"] + pd.to_timedelta(primary["hour"], unit="h")).all())
        check("hourly grain unique", primary["timestamp"].is_unique)
        daily = frames["daily_rentals"].set_index("date").sort_index()
        check("daily grain unique", daily.index.is_unique)
        for column in ["rental_count", "casual_count", "registered_count"]:
            totals = primary.groupby("date")[column].sum().sort_index()
            check(f"hour/day {column} reconciliation", totals.index.equals(daily.index) and totals.eq(daily[column]).all())
        observations = {"missing_calendar_hours": int(len(pd.date_range(primary["timestamp"].min(), primary["timestamp"].max(), freq="h")) - len(primary)),
                        "upstream_page_instances": 17389, "actual_hour_csv_records": len(primary)}
    elif project_id == "bank_marketing":
        check("target labels yes/no", set(primary["subscribed"].unique()) == {"yes", "no"})
        domain(primary, "age", 1, 120)
        for column in ["duration", "pdays", "previous"]:
            check(f"{column} nonnegative", primary[column].ge(0).all())
        check("campaign includes at least one contact", primary["campaign"].ge(1).all())
        observations = {"unknown_category_counts": {column: int(primary[column].eq("unknown").sum())
            for column in primary.select_dtypes(include="string") if primary[column].eq("unknown").any()},
            "pdays_999_not_previously_contacted": int(primary["pdays"].eq(999).sum()),
            "positive_target_rate": float(primary["subscribed"].eq("yes").mean())}
    elif project_id == "student_performance":
        check("subject population", primary["subject"].value_counts().to_dict() == {"portuguese": 649, "mathematics": 395})
        for column in ["g1", "g2", "g3"]:
            domain(primary, column, 0, 20)
        for column in ["medu", "fedu"]:
            domain(primary, column, 0, 4)
        for column in ["studytime", "traveltime"]:
            domain(primary, column, 1, 4)
        for column in ["famrel", "freetime", "goout", "dalc", "walc", "health"]:
            domain(primary, column, 1, 5)
        check("absences nonnegative", primary["absences"].ge(0).all())
    elif project_id == "wine_quality":
        check("wine type population", primary["wine_type"].value_counts().to_dict() == {"white": 4898, "red": 1599})
        domain(primary, "quality", 0, 10)
        check("quality is integer score", primary["quality"].eq(primary["quality"].round()).all())
        domain(primary, "ph", 0, 14)
        for column in set(COLUMNS[project_id]) - {"wine_type"}:
            check(f"{column} nonnegative", primary[column].ge(0).all())
    else:
        check("orientation valid category codes", set(primary["orientation"].unique()) <= {2, 3, 4, 5})
        check("glazing distribution valid codes", set(primary["glazing_area_distribution"].unique()) <= set(range(6)))
        for column in ["surface_area", "wall_area", "roof_area", "overall_height", "heating_load", "cooling_load"]:
            check(f"{column} positive", primary[column].gt(0).all())
        check("simulation configuration unique", not primary.duplicated(
            [column for column in COLUMNS[project_id] if column not in TARGETS[project_id]]).any())
    # Recompute each entire aggregate independently from saved preparation data.
    from ingest_public_datasets import build_mart
    expected_name, expected_mart = build_mart(project_id, frames)
    check("mart name contract", mart_name == expected_name)
    assert_frame_equal(mart.reset_index(drop=True), expected_mart.reset_index(drop=True), check_dtype=False,
                       check_exact=False, rtol=1e-10, atol=1e-8)
    check("mart full reconciliation", True)
    check("mart population reconciles", int(mart["source_records"].sum()) == len(primary))
    return {"schema_version": 1, "project_id": project_id, "status": "passed",
            "checks": checks, "profiles": profiles, "observations": observations}


def validate_saved(project_id, verify_source=False):
    from ingest_public_datasets import fetch, members, prepare, sha256
    project_root = ROOT / "data" / project_id
    catalog = json.loads((project_root / "metadata/data_catalog.json").read_text(encoding="utf-8"))
    source_archive, pin = fetch(project_id, offline=True)
    if catalog["source"]["sha256"] != pin["sha256"]:
        raise ValueError("Catalog source pin differs from lock")
    frames = {}
    for name, dataset in catalog["logical_datasets"].items():
        path = (project_root / dataset["path"]).resolve()
        if not path.is_relative_to(project_root.resolve()):
            raise ValueError("Catalog path escapes project")
        if sha256(path) != dataset["sha256"]:
            raise ValueError(f"{project_id}/{name}: output hash mismatch")
        arrow = pq.read_table(path)
        actual_schema = [{"name": field.name, "type": str(field.type), "nullable": field.nullable} for field in arrow.schema]
        declared_schema = [{key: field[key] for key in ["name", "type", "nullable"]} for field in dataset["schema"]]
        if actual_schema != declared_schema or arrow.num_rows != dataset["rows"]:
            raise ValueError(f"{project_id}/{name}: physical schema/row count differs from catalog")
        if dataset["layer"] == "prepared":
            frames[name] = arrow.to_pandas()
        else:
            mart_name, mart = name, arrow.to_pandas()
    report = validate_frames(project_id, frames, mart_name, mart)
    if verify_source:
        source_frames, _ = prepare(project_id, members(source_archive))
        for name in frames:
            assert_frame_equal(frames[name], source_frames[name], check_dtype=False, check_exact=True)
        report["checks"].append({"name": "all prepared values reconcile with pinned raw source", "status": "passed"})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=sorted(SOURCES))
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    for project_id in ([args.project] if args.project else SOURCES):
        report = validate_saved(project_id, args.verify_source)
        print(f"PASS {project_id}: {len(report['checks'])} checks")


if __name__ == "__main__":
    main()
