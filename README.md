# Data Workbench

Kho dữ liệu dùng chung cho các project học tập về data science và phân tích dữ liệu. Mỗi bộ nằm trong thư mục riêng dưới `data/`, có file dữ liệu, mô tả cột, nguồn và kiểm tra chất lượng. Project thực hành ở nơi khác có thể đọc file trực tiếp, không cần chạy website hay pipeline.

Hiện có **7 project**: Global Superstore có sẵn và **6 bộ UCI mới với 608.785 quan sát bảng chính**. Bảng ngày của Bike Sharing và marts là dữ liệu tổng hợp, không cộng vào số quan sát này.

| Project | Quan sát bảng chính | Bài tập |
| --- | ---: | --- |
| [Online Retail](data/online_retail/README.md) | 541.909 | Data quality, SQL, RFM, market basket, cohort |
| [Bike Sharing](data/bike_sharing/README.md) | 17.379 | Time series, dự báo nhu cầu, regression |
| [Bank Marketing](data/bank_marketing/README.md) | 41.188 | Classification, mất cân bằng lớp, encoding |
| [Student Performance](data/student_performance/README.md) | 1.044 | Regression, thời điểm dự báo, group split |
| [Wine Quality](data/wine_quality/README.md) | 6.497 | Regression, ordinal classification |
| [Energy Efficiency](data/energy_efficiency/README.md) | 768 | Multi-output regression, group holdout |
| [Global Superstore](data/global_superstore/metadata/project.json) | 51.290 | Dimensional modeling, SQL, BI, profitability |

Tra cứu [catalog](data/CATALOG.md), [registry JSON](data/index.json) và [quy ước dữ liệu](data/README.md).

## Sử dụng từ project khác

Đọc Parquet bằng pandas cần `pandas` và `pyarrow` (`python -m pip install pandas pyarrow`).

```python
from pathlib import Path
import pandas as pd

# Đường dẫn tới checkout kho dữ liệu trên máy bạn, độc lập với working directory.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "bank_marketing/prepared/campaign_contacts.parquet")

# Dự báo trước cuộc gọi: duration chỉ biết sau cuộc gọi.
X = df.drop(columns=["record_id", "source_file", "source_row", "duration", "subscribed"])
y = df["subscribed"].eq("yes").astype(int)
# Chia tập phù hợp trước khi fit encoder/imputer/scaler/resampling.
```

R, DuckDB, Polars và Spark cũng có thể đọc trực tiếp. `data/index.json` chứa đường dẫn tính từ repository root cho các bảng của tất cả project. Mỗi bộ UCI có:

```text
data/<project_id>/
├── raw/source.zip                    # Archive nguồn nguyên vẹn
├── prepared/*.parquet                # Observation chuẩn hóa tên/kiểu
├── marts/*.parquet                   # Aggregate từ bảng chính
├── metadata/
│   ├── project.json
│   ├── data_catalog.json
│   ├── data_dictionary.md
│   └── quality_report.json
├── README.md
└── LICENSE.md
```

Raw giữ CSV/Excel gốc trong archive; bank/student có ZIP lồng nhau. Prepared giữ null, dòng trùng, `unknown`/sentinel và nhãn gốc để thực hành. `record_id`, `source_file`, `source_row` chỉ dùng đối chiếu nguồn và cần loại khỏi predictor.

## Tái tạo và kiểm tra dữ liệu UCI

Không cần tái tạo để đọc file đã có. Pipeline yêu cầu Python 3.10+:

```powershell
python -m pip install -r requirements.txt
python scripts/ingest_public_datasets.py --offline
python scripts/validate_public_datasets.py --verify-source
```

Nếu chưa có archive, bỏ `--offline` để tải từ nguồn chính thức. Chọn riêng một bộ bằng `--project wine_quality` (áp dụng cho cả build và validate).

`scripts/public_sources.lock.json` pin URL, SHA-256, kích thước và thời điểm lấy nguồn. Pipeline dừng nếu checksum khác. Thay snapshot cần review nguồn, cập nhật pin, build và validate lại; không tự bỏ qua mismatch.

Validator kiểm tra schema vật lý, checksum, số dòng, key, provenance, nullability, miền giá trị theo domain và mart reconciliation. `--verify-source` đọc lại archive và so toàn bộ giá trị prepared với nguồn. README từng bộ ghi cách chia tập và tránh leakage.

Test regression cho pipeline và điểm đọc từ project khác: `python -m unittest discover -s tests -v`. Cài thêm `duckdb` để chạy cả test thực thi query SQL.

Query mẫu nằm ở `sql/<project_id>_analysis.sql`, gồm kiểm tra grain và phân tích domain. Chạy từ repository root bằng Python với `duckdb`:

```python
import duckdb
query = Path("sql/online_retail_analysis.sql").read_text(encoding="utf-8")
print(duckdb.connect().execute(query).df())
```

Sáu bộ UCI mới có CC BY 4.0, với ghi nguồn và mô tả thay đổi trong LICENSE.md từng bộ. Nguồn/giấy phép Global Superstore cũ chưa được xác minh và không thuộc giấy phép các bộ UCI.

## Trải nghiệm học theo project

Website trong `docs/` hiện có workspace cho Global Superstore, đi qua năm màn hình:

1. **Tổng quan**: đặt câu hỏi kinh doanh và xác định đầu ra.
2. **Tổ chức dữ liệu**: đọc grain, fact, dimension, khóa và partition.
3. **Truy vấn**: đọc Parquet trực tiếp bằng DuckDB và tạo KPI.
4. **EDA**: kiểm tra chất lượng, phân phối, xu hướng và giả thuyết.
5. **Dashboard**: trình bày kết quả từ các phép tổng hợp đã kiểm tra.

Tiến độ học được lưu trong `localStorage` của trình duyệt. Các đoạn SQL có nút sao chép và dashboard dùng dữ liệu thật được xuất từ Parquet.

## Analytical standards

Global Superstore được trình bày như một case study có thể review, không chỉ là dashboard demo:

- **Business framing**: stakeholder problem, analytical contract, decision scope và definition of done.
- **Data architecture**: fact grain, relationship contract, modeling decision log và machine-readable catalog.
- **Quality gates**: uniqueness, referential integrity, measure domain, temporal validity và mart reconciliation.
- **Metric contract**: công thức, denominator, filter context, interpretation và limitation của từng KPI.
- **EDA evidence log**: tách measurement, interpretation, unsupported claim và next test.
- **Decision dashboard**: executive, profitability, customer-market và methodology được tách thành các trang riêng.

Forecast không được công bố khi chưa có rolling-origin backtest và accuracy report. Các liên hệ giữa discount, shipping cost và profit được mô tả như association, không được diễn giải thành causal effect.

## Cấu trúc repository

```text
data-workbench/
├── data/                              # Có CATALOG.md và index.json
│   └── global_superstore/             # Dimensional model có sẵn
│       ├── dimensions/                 # Entity tham chiếu
│       ├── facts/                      # Event, có thể Hive partition
│       ├── marts/                      # Aggregate cho dashboard
│       └── metadata/
│           ├── project.json            # Thông tin và learning path
│           └── data_catalog.json       # Schema, grain, key, relationship
├── sql/                                # Truy vấn mẫu theo project
├── scripts/                            # Build, validate và xuất web asset
├── docs/                               # Website GitHub Pages
└── README.md
```

Sáu project UCI dùng cấu trúc raw/prepared/marts/metadata ở trên. Quy ước chi tiết nằm tại [data/README.md](data/README.md).

## Chạy project Global Superstore

Yêu cầu Python 3.10+ với `pandas` và `pyarrow`.

```powershell
python scripts/convert_csv_to_parquet.py
python scripts/validate_model.py
python scripts/build_dashboard_assets.py
```

Validator sẽ dừng nếu phát hiện duplicate primary key, orphan key, measure null, quantity không dương, sales hoặc shipping cost âm, discount ngoài `[0, 1]`, ship date trước order date, hoặc mart không reconcile với fact.

Chạy website ở local:

```powershell
python -m http.server 8000 --directory docs
```

Sau đó mở `http://localhost:8000/global-superstore/`.

## Truy vấn bằng DuckDB

Cài DuckDB nếu cần:

```powershell
pip install duckdb
duckdb
```

Trong DuckDB CLI:

```sql
.read sql/demo_analysis.sql
```

Ví dụ đọc fact đã partition theo năm:

```sql
SELECT order_year, SUM(sales) AS sales, SUM(profit) AS profit
FROM read_parquet(
  'data/global_superstore/facts/fact_order_line/**/*.parquet',
  hive_partitioning = true
)
WHERE order_year = 2014
GROUP BY order_year;
```

## Thêm project phân tích mới

Tạo bộ khung bằng script:

```powershell
python scripts/scaffold_project.py customer_churn "Customer Churn" --domain crm_analytics
```

Thêm `--storage-model tabular_snapshot` để tạo raw/prepared/marts/metadata cho bộ observation dùng trong data science. Xác minh nguồn và giấy phép trước khi đưa dữ liệu vào kho. Với UCI trong pipeline mới, thêm source contract vào `scripts/public_dataset_specs.py`, reader vào `ingest_public_datasets.py`, validator domain vào `validate_public_datasets.py` và query/mart vào `dataset_documentation.py`.

Sau đó:

1. Đưa Parquet vào đúng layer trong `data/customer_churn/`.
2. Khai báo grain, schema, primary key và relationship trong `metadata/data_catalog.json`.
3. Viết pipeline build và validator riêng cho domain.
4. Thêm query mẫu vào `sql/customer_churn_analysis.sql`.
5. Viết README, từ điển dữ liệu, ghi nguồn/giấy phép và báo cáo chất lượng, cập nhật catalog/registry.
6. Nếu muốn có workspace trên website, xuất JSON nhẹ và tạo route `docs/customer-churn/`, rồi đăng ký trong `docs/index.html`.

Không trộn file của nhiều domain trong cùng một thư mục. Khi cần phân tích liên domain, dùng conformed dimension và ghi mapping rõ trong catalog.

## GitHub Pages

Hướng dẫn publish nằm tại [docs/README.md](docs/README.md). Source of truth vẫn là Parquet; JSON trong `docs/assets/data/` chỉ là aggregate nhẹ dành cho trình duyệt.
