"""Download reviewed UCI archives and build portable, documented Parquet snapshots.

Raw archives are immutable and pinned in public_sources.lock.json. Reads never
extract untrusted ZIP paths to disk. A failed download cannot replace a snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import ZipFile, is_zipfile

import pandas as pd
from public_dataset_specs import COMMON, COLUMNS, SOURCES

ROOT = Path(__file__).resolve().parents[1]
LOCK = Path(__file__).with_name("public_sources.lock.json")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(project_id, offline=False):
    source = SOURCES[project_id]
    path = ROOT / "data" / project_id / "raw" / "source.zip"
    pins = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    pin = pins.get(project_id)
    if pin and pin["download_url"] != source["download_url"]:
        raise ValueError(f"{project_id}: URL changed; review source pin explicitly")
    if not path.exists():
        if offline:
            raise FileNotFoundError(f"Offline source is missing: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".download")
        for attempt in range(3):
            try:
                request = Request(source["download_url"], headers={"User-Agent": "DataWorkbench-learning-datasets/1.0"})
                with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                    size = 0
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if size > 100 * 1024 * 1024:
                            raise ValueError("Source exceeds the 100 MiB snapshot limit")
                        output.write(chunk)
                if not is_zipfile(temporary):
                    raise ValueError("Upstream returned a non-ZIP response")
                if pin and sha256(temporary) != pin["sha256"]:
                    raise ValueError(f"{project_id}: upstream content changed; reviewed snapshot required")
                temporary.replace(path)
                break
            except (URLError, HTTPError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
            finally:
                temporary.unlink(missing_ok=True)
    digest = sha256(path)
    if pin and digest != pin["sha256"]:
        raise ValueError(f"{project_id}: cached archive SHA-256 mismatch")
    if not pin:
        pins[project_id] = {
            "download_url": source["download_url"], "sha256": digest,
            "size_bytes": path.stat().st_size,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        write_json(LOCK, pins)
    print(f"Source verified: {project_id} ({path.stat().st_size:,} bytes)", flush=True)
    return path, pins[project_id]


def members(archive, prefix="source.zip", depth=0):
    if depth > 2:
        raise ValueError("Unexpected archive nesting")
    result = {}
    with ZipFile(archive) as zipped:
        if sum(item.file_size for item in zipped.infolist()) > 300 * 1024 * 1024:
            raise ValueError("Archive expands beyond the 300 MiB limit")
        for item in zipped.infolist():
            if item.is_dir() or item.filename.startswith("__MACOSX/"):
                continue
            payload = zipped.read(item)
            name = f"{prefix}!{item.filename}"
            if item.filename.endswith(".zip"):
                result.update(members(io.BytesIO(payload), name, depth + 1))
            else:
                result[name] = payload
    return result


def find_member(contents, filename):
    matches = [(name, data) for name, data in contents.items() if name.split("!")[-1].split("/")[-1] == filename]
    if len(matches) != 1:
        raise ValueError(f"Expected one {filename} in source, found {len(matches)}")
    return matches[0]


def load_csv(contents, filename, **kwargs):
    name, payload = find_member(contents, filename)
    frame = pd.read_csv(io.BytesIO(payload), **kwargs)
    return frame, name


def snake(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def provenance(frame, member):
    frame = frame.copy()
    filename = member.split("!")[-1].split("/")[-1]
    frame.insert(0, "source_row", range(1, len(frame) + 1))
    frame.insert(0, "source_file", filename)
    frame.insert(0, "record_id", [f"{Path(filename).stem}:{i:06d}" for i in range(1, len(frame) + 1)])
    for column in frame.select_dtypes(include="object").columns:
        frame[column] = frame[column].astype("string")
    return frame


def prepare(project_id, contents):
    lineage = {}
    def table(name, frame, member):
        lineage.setdefault(name, []).append(member)
        return provenance(frame, member)

    if project_id == "online_retail":
        member, payload = find_member(contents, "Online Retail.xlsx")
        frame = pd.read_excel(io.BytesIO(payload), engine="openpyxl", sheet_name="Online Retail",
                              dtype={"InvoiceNo": "string", "StockCode": "string", "CustomerID": "string"})
        frame = frame.rename(columns={"InvoiceNo": "invoice_no", "StockCode": "stock_code",
            "Description": "description", "Quantity": "quantity", "InvoiceDate": "invoice_date",
            "UnitPrice": "unit_price_gbp", "CustomerID": "customer_id", "Country": "country"})
        frame["customer_id"] = frame["customer_id"].str.replace(r"\.0$", "", regex=True)
        frame["invoice_date"] = pd.to_datetime(frame["invoice_date"], errors="raise")
        frame["is_cancellation"] = frame["invoice_no"].str.upper().str.startswith("C")
        frame["line_amount_gbp"] = frame["quantity"] * frame["unit_price_gbp"]
        frames = {"invoice_lines": table("invoice_lines", frame, member)}
    elif project_id == "bike_sharing":
        frames = {}
        renames = {"dteday": "date", "yr": "year_code", "mnth": "month", "hr": "hour",
            "workingday": "working_day", "weathersit": "weather_situation", "temp": "temperature_normalized",
            "atemp": "feels_like_normalized", "hum": "humidity_normalized", "windspeed": "windspeed_normalized",
            "casual": "casual_count", "registered": "registered_count", "cnt": "rental_count"}
        for filename, name in [("hour.csv", "hourly_rentals"), ("day.csv", "daily_rentals")]:
            frame, member = load_csv(contents, filename)
            frame = frame.rename(columns=renames)
            frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise")
            if "hour" in frame:
                frame["timestamp"] = frame["date"] + pd.to_timedelta(frame["hour"], unit="h")
            frames[name] = table(name, frame, member)
    elif project_id == "bank_marketing":
        frame, member = load_csv(contents, "bank-additional-full.csv", sep=";")
        frame = frame.rename(columns={name: snake(name) for name in frame.columns}).rename(columns={"y": "subscribed"})
        frames = {"campaign_contacts": table("campaign_contacts", frame, member)}
    elif project_id in {"student_performance", "wine_quality"}:
        student = project_id == "student_performance"
        name = "subject_results" if student else "wine_samples"
        parts = []
        variants = [("student-mat.csv", "mathematics"), ("student-por.csv", "portuguese")] if student else [
            ("winequality-red.csv", "red"), ("winequality-white.csv", "white")]
        for filename, variant in variants:
            frame, member = load_csv(contents, filename, sep=";")
            frame = frame.rename(columns={column: snake(column) for column in frame.columns})
            frame.insert(0, "subject" if student else "wine_type", variant)
            parts.append(table(name, frame, member))
        frames = {name: pd.concat(parts, ignore_index=True)}
    elif project_id == "energy_efficiency":
        member, payload = find_member(contents, "ENB2012_data.xlsx")
        frame = pd.read_excel(io.BytesIO(payload), engine="openpyxl", usecols="A:J")
        if list(frame.columns) != [f"X{i}" for i in range(1, 9)] + ["Y1", "Y2"]:
            raise ValueError("Energy workbook schema changed")
        # Blank trailing worksheet rows are not observations. No partial rows dropped.
        frame = frame.dropna(how="all").rename(columns=dict(zip(frame.columns, COLUMNS[project_id])))
        for column in ["orientation", "glazing_area_distribution"]:
            if not frame[column].eq(frame[column].round()).all():
                raise ValueError(f"Non-integer category code: {column}")
            frame[column] = frame[column].astype("int64")
        frames = {"building_simulations": table("building_simulations", frame, member)}
    else:
        raise ValueError(project_id)
    for name, frame in frames.items():
        undocumented = set(frame) - set(COMMON) - set(COLUMNS[project_id])
        if undocumented:
            raise ValueError(f"Undocumented columns: {undocumented}")
    return frames, lineage


def build_mart(project_id, frames):
    """Aggregates preserve the complete population; no silent cleaning."""
    primary = frames[SOURCES[project_id]["primary_table"]]
    if project_id == "online_retail":
        frame = primary.assign(month=primary["invoice_date"].dt.to_period("M").dt.to_timestamp())
        mart = frame.groupby("month", as_index=False).agg(
            source_records=("record_id", "size"), invoices=("invoice_no", "nunique"),
            identified_customers=("customer_id", "nunique"), cancellation_lines=("is_cancellation", "sum"),
            signed_quantity=("quantity", "sum"), signed_amount_gbp=("line_amount_gbp", "sum"))
        return "monthly_transactions", mart
    if project_id == "bike_sharing":
        frame = primary.assign(month=primary["date"].dt.to_period("M").dt.to_timestamp())
        mart = frame.groupby("month", as_index=False).agg(
            source_records=("record_id", "size"), rental_count=("rental_count", "sum"),
            casual_count=("casual_count", "sum"), registered_count=("registered_count", "sum"))
        return "monthly_rentals", mart
    if project_id == "bank_marketing":
        frame = primary.assign(subscribed_yes=primary["subscribed"].eq("yes").astype("int64"))
        mart = frame.groupby(["contact", "poutcome"], as_index=False).agg(
            source_records=("record_id", "size"), subscribers=("subscribed_yes", "sum"))
        mart["subscription_rate"] = mart["subscribers"] / mart["source_records"]
        return "channel_outcomes", mart
    if project_id == "student_performance":
        return "subject_grade_summary", primary.groupby(["subject", "school"], as_index=False).agg(
            source_records=("record_id", "size"), mean_g3=("g3", "mean"), mean_absences=("absences", "mean"))
    if project_id == "wine_quality":
        return "quality_distribution", primary.groupby(["wine_type", "quality"], as_index=False).agg(
            source_records=("record_id", "size"), mean_alcohol=("alcohol", "mean"))
    return "orientation_load_summary", primary.groupby("orientation", as_index=False).agg(
        source_records=("record_id", "size"), mean_heating_load=("heating_load", "mean"),
        mean_cooling_load=("cooling_load", "mean"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=sorted(SOURCES), help="Only process this project")
    parser.add_argument("--offline", action="store_true", help="Use cached pinned archives without network")
    parser.add_argument("--download-only", action="store_true")
    args = parser.parse_args()
    for project_id in ([args.project] if args.project else SOURCES):
        archive, pin = fetch(project_id, args.offline)
        if args.download_only:
            continue
        frames, lineage = prepare(project_id, members(archive))
        # Import here so downloading sources does not need validation/report modules.
        from validate_public_datasets import validate_frames
        from dataset_documentation import publish_project, publish_registry
        mart_name, mart = build_mart(project_id, frames)
        report = validate_frames(project_id, frames, mart_name, mart)
        publish_project(project_id, frames, lineage, mart_name, mart, pin, report)
        print(f"Built {project_id}: {len(frames[SOURCES[project_id]['primary_table']]):,} primary records", flush=True)
    if not args.download_only:
        publish_registry()


if __name__ == "__main__":
    main()
