# Data Workbench

Kho database demo cho các project phân tích dữ liệu nhỏ. Mỗi project chứa dữ liệu Parquet độc lập, data catalog, truy vấn mẫu, quy trình EDA và một dashboard kết quả.

Project mẫu hiện có: **Global Superstore**, gồm 51.290 line items trong giai đoạn 2011-2014.

## Trải nghiệm học theo project

Website trong `docs/` không chỉ hiển thị dashboard. Mỗi project đi qua năm màn hình:

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
├── data/
│   └── <project_id>/
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

Quy ước chi tiết nằm tại [data/README.md](data/README.md).

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

Sau đó:

1. Đưa Parquet vào đúng layer trong `data/customer_churn/`.
2. Khai báo grain, schema, primary key và relationship trong `metadata/data_catalog.json`.
3. Viết pipeline build và validator riêng cho domain.
4. Thêm query mẫu vào `sql/customer_churn_analysis.sql`.
5. Xuất JSON nhẹ cho trình duyệt và tạo route `docs/customer-churn/`.
6. Đăng ký project trên trang thư viện trong `docs/index.html`.

Không trộn file của nhiều domain trong cùng một thư mục. Khi cần phân tích liên domain, dùng conformed dimension và ghi mapping rõ trong catalog.

## GitHub Pages

Hướng dẫn publish nằm tại [docs/README.md](docs/README.md). Source of truth vẫn là Parquet; JSON trong `docs/assets/data/` chỉ là aggregate nhẹ dành cho trình duyệt.
