"""Publish data artifacts, source attribution, catalogs and learner entry points."""
from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from public_dataset_specs import COMMON, COLUMNS, GRAINS, LICENSE_URL, SOURCES, TARGETS, VERIFIED_ON

ROOT = Path(__file__).resolve().parents[1]

SQL_ANALYSES = {
    "online_retail": """-- All original rows, including corrections and duplicates; signed source values.
SELECT date_trunc('month', invoice_date) AS month,
       count(*) AS lines, count(DISTINCT invoice_no) AS invoices,
       sum(line_amount_gbp) AS signed_amount_gbp,
       count(*) FILTER (WHERE customer_id IS NULL) AS missing_customer_lines
FROM source_data GROUP BY 1 ORDER BY 1;
-- December 2011 is partial. Define cancellation/deduplication policies before RFM.
""",
    "bike_sharing": """SELECT hour, working_day, count(*) AS observed_hours,
       avg(rental_count) AS mean_rentals
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- Forecast target rental_count without casual_count/registered_count.
-- Missing hours are not automatically zero-demand hours.
""",
    "bank_marketing": """SELECT contact, poutcome, count(*) AS observations,
       count(*) FILTER (WHERE subscribed = 'yes') AS subscribers,
       avg(CASE WHEN subscribed = 'yes' THEN 1.0 ELSE 0.0 END) AS subscription_rate
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- duration is unavailable before the call: exclude it from pre-call prediction.
""",
    "student_performance": """SELECT subject, school, count(*) AS subject_observations,
       avg(g3) AS mean_final_grade, avg(absences) AS mean_absences
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- Counts are subject observations, not distinct students.
-- g1/g2 are available only after their grading periods.
""",
    "wine_quality": """SELECT wine_type, quality, count(*) AS samples, avg(alcohol) AS mean_alcohol
FROM source_data GROUP BY 1, 2 ORDER BY 1, 2;
-- Keep repeated feature vectors in the same split when benchmarking models.
""",
    "energy_efficiency": """SELECT orientation, count(*) AS configurations,
       avg(heating_load) AS mean_heating_load, avg(cooling_load) AS mean_cooling_load
FROM source_data GROUP BY 1 ORDER BY 1;
-- These are simulation results. Both load columns are targets in multi-output tasks.
""",
}

MART_DESCRIPTIONS = {
    "month": "Tháng quan sát, lưu ngày đầu tháng.",
    "source_records": "Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng.",
    "invoices": "Số invoice_no distinct trong tháng, gồm hóa đơn hủy.",
    "identified_customers": "Số customer_id distinct không null trong tháng; không cộng qua các tháng.",
    "cancellation_lines": "Số dòng có cờ hủy theo prefix hóa đơn.",
    "signed_quantity": "Tổng quantity có dấu của tất cả dòng trong nhóm.",
    "signed_amount_gbp": "Tổng quantity × unit_price_gbp của tất cả dòng, GBP.",
    "rental_count": "Tổng lượt thuê của các giờ quan sát trong tháng.",
    "casual_count": "Tổng lượt thuê khách vãng lai của các giờ quan sát trong tháng.",
    "registered_count": "Tổng lượt thuê khách đăng ký của các giờ quan sát trong tháng.",
    "subscribers": "Số quan sát subscribed = yes trong nhóm.",
    "subscription_rate": "subscribers / source_records tại đúng nhóm, không lấy trung bình các tỷ lệ.",
    "mean_g3": "Trung bình g3 của các quan sát môn học trong nhóm.",
    "mean_absences": "Trung bình absences của các quan sát môn học trong nhóm.",
    "mean_alcohol": "Trung bình alcohol theo wine_type × quality.",
    "mean_heating_load": "Trung bình heating_load theo orientation.",
    "mean_cooling_load": "Trung bình cooling_load theo orientation.",
}

MART_KEYS = {
    "online_retail": ["month"], "bike_sharing": ["month"],
    "bank_marketing": ["contact", "poutcome"], "student_performance": ["subject", "school"],
    "wine_quality": ["wine_type", "quality"], "energy_efficiency": ["orientation"],
}

EXCLUDED = {
    "online_retail": [], "bike_sharing": ["instant", "casual_count", "registered_count"],
    "bank_marketing": ["duration"], "student_performance": ["g1", "g2"],
    "wine_quality": [], "energy_efficiency": [],
}


def source_column(project_id, column):
    if column in COMMON or column in {"subject", "wine_type", "timestamp", "is_cancellation", "line_amount_gbp"}:
        return None
    special = {
        "online_retail": dict(zip(
            ["invoice_no", "stock_code", "description", "quantity", "invoice_date", "unit_price_gbp", "customer_id", "country"],
            ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"])),
        "bike_sharing": {"date": "dteday", "year_code": "yr", "month": "mnth", "hour": "hr",
            "working_day": "workingday", "weather_situation": "weathersit", "temperature_normalized": "temp",
            "feels_like_normalized": "atemp", "humidity_normalized": "hum", "windspeed_normalized": "windspeed",
            "casual_count": "casual", "registered_count": "registered", "rental_count": "cnt"},
        "bank_marketing": {"subscribed": "y", "emp_var_rate": "emp.var.rate", "cons_price_idx": "cons.price.idx",
            "cons_conf_idx": "cons.conf.idx", "nr_employed": "nr.employed"},
        "student_performance": {key.lower(): key for key in ["Medu", "Fedu", "Mjob", "Fjob", "Pstatus", "Dalc", "Walc", "G1", "G2", "G3"]},
        "wine_quality": {key.replace(" ", "_").lower(): key for key in ["fixed acidity", "volatile acidity", "citric acid",
            "residual sugar", "free sulfur dioxide", "total sulfur dioxide", "pH"]},
        "energy_efficiency": dict(zip(COLUMNS[project_id], [f"X{i}" for i in range(1, 9)] + ["Y1", "Y2"])),
    }
    return special[project_id].get(column, column)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def publish_project(project_id, frames, lineage, mart_name, mart, pin, report):
    from ingest_public_datasets import sha256
    source = SOURCES[project_id]
    project_root = ROOT / "data" / project_id
    logical = {}
    files = []
    for name, frame in {**frames, mart_name: mart}.items():
        layer = "prepared" if name in frames else "marts"
        relative_path = f"{layer}/{name}.parquet"
        destination = project_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        arrow = pa.Table.from_pandas(frame, preserve_index=False)
        nullable = {"description", "customer_id"} if project_id == "online_retail" and layer == "prepared" else set()
        schema = pa.schema([pa.field(field.name, field.type, nullable=field.name in nullable) for field in arrow.schema], metadata=arrow.schema.metadata)
        arrow = arrow.cast(schema)
        temporary = destination.with_suffix(".tmp")
        pq.write_table(arrow, temporary, compression="zstd", use_dictionary=True, write_statistics=True, row_group_size=50000)
        temporary.replace(destination)
        fields = []
        for field in arrow.schema:
            if layer == "prepared":
                description = {**COMMON, **COLUMNS[project_id]}[field.name]
                role = "identifier" if field.name in COMMON or field.name == "instant" else (
                    "target" if field.name in TARGETS.get(project_id, []) else "feature")
                if field.name in EXCLUDED[project_id]:
                    role = "unavailable_at_default_prediction_time"
            else:
                description = MART_DESCRIPTIONS.get(field.name, COLUMNS[project_id].get(field.name))
                role = "group_key" if field.name in MART_KEYS[project_id] else "aggregate"
            if not description:
                raise ValueError(f"No dictionary entry for {name}.{field.name}")
            fields.append({"name": field.name, "type": str(field.type), "nullable": field.nullable,
                "role": role, "description": description,
                "source_column": source_column(project_id, field.name) if layer == "prepared" else None})
        logical[name] = {
            "layer": layer, "path": relative_path, "rows": len(frame),
            "grain": GRAINS[name] if layer == "prepared" else "Một dòng cho mỗi nhóm " + " × ".join(MART_KEYS[project_id]),
            "primary_key": ["record_id"] if layer == "prepared" else MART_KEYS[project_id],
            "schema": fields, "sha256": sha256(destination), "size_bytes": destination.stat().st_size,
            "lineage": lineage[name] if layer == "prepared" else [source["primary_table"]],
        }
        files.append({"path": destination.relative_to(ROOT).as_posix(), "rows": len(frame),
                      "size_bytes": destination.stat().st_size, "sha256": logical[name]["sha256"], "compression": "zstd"})
    source_info = {"provider": "UCI Machine Learning Repository", "uci_id": source["uci_id"],
        "source_url": source["source_url"], "doi": source["doi"], "citation": source["citation"],
        "publication_citation": source.get("publication_citation"),
        "license": "CC-BY-4.0", "license_url": LICENSE_URL, "license_verified_on": VERIFIED_ON,
        "archive_path": "raw/source.zip", **pin}
    manifest = {"schema_version": 1, "id": project_id, "slug": project_id.replace("_", "-"),
        "name": source["name"], "domain": source["domain"], "difficulty": "beginner_to_intermediate",
        "status": "data_ready", "storage_model": "tabular_snapshot", "tasks": source["tasks"],
        "description": source["questions"][0], "primary_dataset": source["primary_table"],
        "primary_rows": len(frames[source["primary_table"]]), "source": source_info,
        "business_questions": source["questions"], "learning_guidance": source["guidance"],
        "ml_contract": {"targets": TARGETS.get(project_id, []),
            "technical_columns_to_exclude": ["record_id", "source_file", "source_row"],
            "exclude_at_default_prediction_time": EXCLUDED[project_id],
            "preprocessing": "No fitted imputation, encoding, scaling, resampling or train/test split. Fit only on learner training data."},
        "learning_path": [
            {"id": "quality", "title": "Đọc nguồn và kiểm tra chất lượng", "output": "Quy tắc xử lý null, trùng, sentinel và outlier"},
            {"id": "eda", "title": "SQL và EDA", "output": "Kết quả truy vấn có grain và denominator đúng"},
            {"id": "model", "title": "Phân tích hoặc mô hình", "output": "Baseline, validation phù hợp và báo cáo giới hạn"}],
    }
    catalog = {"schema_version": 1, "project_id": project_id, "model_version": "1.0.0",
        "storage_format": "Parquet / Zstandard", "source": source_info,
        "processing": ["Select only source members listed in each dataset lineage.",
            "Preserve original observation order and values. Normalize column names and parse physical types.",
            "Append technical source_file/source_row/record_id. Append documented derived columns only.",
            "Retain nulls, duplicates, unknown categories and sentinel values. Do not fit preprocessing.",
            "For Energy Efficiency, ignore trailing empty Excel columns and completely blank rows.",
            "Recompute marts from the full primary prepared table; no deduplication."],
        "logical_datasets": logical, "relationships": [], "files": files,
        "quality_report": "metadata/quality_report.json"}
    write_json(project_root / "metadata/project.json", manifest)
    write_json(project_root / "metadata/data_catalog.json", catalog)
    write_json(project_root / "metadata/quality_report.json", report)

    dictionary = [f"# Từ điển dữ liệu — {source['name']}", "",
        "Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.", ""]
    for name, dataset in logical.items():
        dictionary += [f"## `{name}`", "", dataset["grain"], "",
            "| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |", "| --- | --- | --- | --- | --- | --- |"]
        for field in dataset["schema"]:
            dictionary.append(f"| `{field['name']}` | {field['source_column'] or 'derived/aggregate'} | {field['type']} | {'yes' if field['nullable'] else 'no'} | {field['role']} | {field['description']} |")
        dictionary.append("")
    (project_root / "metadata/data_dictionary.md").write_text("\n".join(dictionary), encoding="utf-8")

    license_text = f"""# Giấy phép và ghi nguồn

Dữ liệu nguồn và bản chuyển đổi trong thư mục này: **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

- [Trang dataset]({source['source_url']})
- [Điều khoản giấy phép]({LICENSE_URL})
- [DOI]({source['doi']})
- Ghi nguồn: {source['citation']} {source['doi']}
- Giấy phép được kiểm tra trên trang UCI ngày {VERIFIED_ON}.

{source.get('publication_citation', '')}

Thay đổi của kho: đổi tên cột, chuẩn hóa kiểu dữ liệu, thêm khóa/provenance và các cột derived được mô tả trong catalog, tạo Parquet và mart. Không thay đổi nhãn target hoặc xóa quan sát không hợp lệ. Energy Efficiency bỏ phần worksheet hoàn toàn trống.

Khi chia sẻ bản gốc hoặc bản đã xử lý, giữ ghi nguồn, liên kết giấy phép và mô tả các thay đổi của bạn. Ghi nguồn không hàm ý tác giả hay UCI bảo trợ project này.
"""
    (project_root / "LICENSE.md").write_text(license_text, encoding="utf-8")
    primary = source["primary_table"]
    sql = f"""-- Run with DuckDB from repository root. Each query returns a reviewable result.
CREATE OR REPLACE TEMP VIEW source_data AS
SELECT * FROM read_parquet('data/{project_id}/prepared/{primary}.parquet');

-- Grain check: expected rows = distinct_records, null_keys = 0.
SELECT count(*) AS rows, count(DISTINCT record_id) AS distinct_records,
       count(*) FILTER (WHERE record_id IS NULL) AS null_keys
FROM source_data;

{SQL_ANALYSES[project_id]}"""
    (ROOT / "sql").mkdir(exist_ok=True)
    (ROOT / "sql" / f"{project_id}_analysis.sql").write_text(sql, encoding="utf-8")
    row_table = "\n".join(f"| [{name}]({dataset['path']}) | {dataset['rows']:,} | {dataset['layer']} | {dataset['grain']} |" for name, dataset in logical.items())
    questions = "\n".join(f"- {item}" for item in source["questions"])
    guidance = "\n".join(f"- {item}" for item in source["guidance"])
    profile = report["profiles"][primary]
    nonzero_nulls = {key: value for key, value in profile["null_counts"].items() if value}
    readme = f"""# {source['name']}

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
{row_table}

## Nguồn và tái sử dụng

{source['citation']} [DOI]({source['doi']}). Nguồn: [UCI]({source['source_url']}). Giấy phép: [CC BY 4.0]({LICENSE_URL}), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `{pin['sha256']}`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "{project_id}/prepared/{primary}.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

{questions}

## Quy tắc phân tích và mô hình

{guidance}

## Chất lượng snapshot

Validator đã vượt qua {len(report['checks'])} kiểm tra. Bảng chính có {profile['duplicate_value_rows_after_first']:,} dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{json.dumps(nonzero_nulls, ensure_ascii=False)}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project {project_id} --offline
python scripts/validate_public_datasets.py --project {project_id} --verify-source
```

Query mẫu: [sql/{project_id}_analysis.sql](../../sql/{project_id}_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/{project_id}_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
"""
    (project_root / "README.md").write_text(readme, encoding="utf-8")


def publish_registry():
    entries = []
    for directory in sorted((ROOT / "data").iterdir()):
        manifest_path = directory / "metadata/project.json"
        if not directory.is_dir() or not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") not in {"data_ready", "published"}:
            continue
        catalog = json.loads((directory / "metadata/data_catalog.json").read_text(encoding="utf-8"))
        logical = catalog["logical_datasets"]
        parquet_files = list(directory.rglob("*.parquet"))
        primary_dataset = manifest.get("primary_dataset", "fact_order_line")
        primary_rows = manifest.get("primary_rows")
        if primary_rows is None:
            # The legacy dimensional catalog's fact is partitioned.
            primary_rows = sum(pq.ParquetFile(path).metadata.num_rows for path in (directory / "facts/fact_order_line").rglob("*.parquet"))
        entries.append({"id": manifest["id"], "name": manifest["name"], "domain": manifest["domain"],
            "status": manifest["status"], "primary_dataset": primary_dataset, "primary_rows": primary_rows,
            "parquet_files": len(parquet_files), "parquet_size_bytes": sum(path.stat().st_size for path in parquet_files),
            "datasets": {name: f"data/{directory.name}/" + (
                dataset["path"] if dataset["path"].startswith(dataset["layer"] + "/")
                else f"{dataset['layer']}/{dataset['path']}") for name, dataset in logical.items()},
            "readme": f"data/{directory.name}/README.md" if (directory / "README.md").exists() else "data/README.md",
            "catalog": f"data/{directory.name}/metadata/data_catalog.json",
            "source_url": manifest.get("source", {}).get("source_url"),
            "license": manifest.get("source", {}).get("license", "not_verified"),
            "license_note": "See project LICENSE.md" if "source" in manifest else "Legacy source license has not been verified; not covered by the new CC-BY-4.0 datasets."})
    write_json(ROOT / "data/index.json", {"schema_version": 1, "projects": entries})
    table = "\n".join(f"| [{item['name']}]({item['id']}/README.md) | {item['id']} | {item['primary_rows']:,} | {item['parquet_files']} | {item['license']} |"
        if item["id"] in SOURCES else f"| [{item['name']}](global_superstore/metadata/project.json) | {item['id']} | {item['primary_rows']:,} | {item['parquet_files']} | {item['license']} |"
        for item in entries)
    text = f"""# Catalog dữ liệu thực hành

Mỗi project có thư mục riêng trong `data/`. Tra cứu bằng máy qua [index.json](index.json).

| Project | Thư mục | Quan sát bảng chính | File Parquet | Giấy phép nguồn |
| --- | --- | ---: | ---: | --- |
{table}

Số quan sát lấy từ bảng chính, không cộng dimension, aggregate hoặc bảng ngày/giờ cùng nguồn. Tổng 6 project UCI mới: {sum(item['primary_rows'] for item in entries if item['id'] in SOURCES):,} quan sát bảng chính. Global Superstore là project có sẵn và có {next(item['primary_rows'] for item in entries if item['id'] == 'global_superstore'):,} dòng giao dịch riêng.

`data_ready` nghĩa là có dữ liệu, nguồn, từ điển, validator và truy vấn để thực hành từ project khác. Website `docs/` hiện có workspace hướng dẫn riêng cho Global Superstore.

## Chọn theo bài tập

| Kỹ năng | Bộ dữ liệu | Lưu ý chính |
| --- | --- | --- |
| SQL, data quality, RFM, market basket, cohort | Online Retail | Null ID, hoàn/hủy, trùng và tháng cuối chưa đủ |
| Time series, seasonality, demand forecasting | Bike Sharing | Split theo thời gian, giờ thiếu, leakage từ thành phần target |
| Classification, imbalanced learning, category | Bank Marketing | Loại duration trước cuộc gọi, giữ unknown và pdays=999 |
| Regression, đánh giá theo môn/nhóm | Student Performance | Quan sát môn học khác số học sinh, thời điểm biết G1/G2 |
| Regression, ordinal classification | Wine Quality | Quality không cân bằng, vector feature trùng |
| Multi-output regression, group holdout | Energy Efficiency | Dữ liệu mô phỏng, target kép, shape holdout |
| Dimensional modeling, BI, profitability | Global Superstore | Grain, join key và reconcile marts |

Giấy phép của từng bộ áp dụng độc lập. Các bộ UCI mới có ghi nguồn và mô tả thay đổi trong LICENSE.md. Nguồn/giấy phép của Global Superstore cũ chưa được xác minh, không tự áp giấy phép của UCI cho bộ đó.
"""
    (ROOT / "data/CATALOG.md").write_text(text, encoding="utf-8")
