# Global Superstore Analytics Lakehouse

Đây là project phân tích dữ liệu mẫu theo mô hình dimensional analytics có thể chạy trực tiếp bằng DuckDB, Power BI, Spark hoặc Polars. Parquet là nguồn dữ liệu chuẩn; không có database engine bắt buộc phải cài kèm.

## Cấu trúc dữ liệu

```text
data/
├── README.md
└── global_superstore/                 # Một data domain độc lập
    ├── dimensions/                    # Bảng tham chiếu, một file/entity
    │   ├── dim_date.parquet
    │   ├── dim_customer.parquet
    │   ├── dim_product.parquet
    │   ├── dim_geography.parquet
    │   ├── dim_ship_mode.parquet
    │   └── dim_order_priority.parquet
    ├── facts/                         # Sự kiện; Hive partition theo order_year
    │   ├── fact_order/order_year=YYYY/part-00000.parquet
    │   └── fact_order_line/order_year=YYYY/part-00000.parquet
    ├── marts/                         # KPI tổng hợp cho dashboard nhanh
    │   ├── monthly_sales_kpis.parquet
    │   └── country_sales_kpis.parquet
    └── metadata/data_catalog.json     # Schema, grain, khoá và quan hệ
```

Mỗi data domain sau này dùng cùng layout `data/<domain_name>/{dimensions,facts,marts,metadata}`. Ví dụ dữ liệu Returns hoặc Marketing được thêm ở `data/returns/...` hay `data/marketing/...`, không trộn file với Global Superstore. Khi cần phân tích liên domain, dùng các conformed dimension (chẳng hạn `dim_date`, `dim_customer`) và ghi rõ mapping trong catalog của domain mới.

## Mô hình dữ liệu

```text
 dim_date (2 vai trò) ──────┐
 dim_customer ─────────────┤
 dim_geography ────────────┤
 dim_ship_mode ────────────┤
 dim_order_priority ───────┤
                             ▼
                       fact_order ────< fact_order_line >──── dim_product
```

- `fact_order` có grain là một order header duy nhất.
- `fact_order_line` có grain là một dòng giao dịch và chứa các measure `sales`, `quantity`, `discount`, `profit`, `shipping_cost`.
- Dimension và fact có primary key/foreign key rõ ràng. `data_catalog.json` là data contract có thể đọc bằng máy.
- Fact được partition theo `order_year` kiểu Hive. Giá trị partition không lặp trong file, nên query engine có thể loại cả thư mục trước khi quét Parquet.
- Parquet dùng Zstandard, dictionary encoding, statistics và row group 10.000 dòng.

`Order ID` và `Product ID` của CSV nguồn không luôn duy nhất trên toàn bộ dataset. Vì thế mô hình giữ chúng như business attribute, còn `*_key` là hash key xác định theo natural grain. Build sẽ dừng nếu có duplicate key hoặc bản ghi mồ côi.

## Chạy lại pipeline

Yêu cầu Python 3.10+ với `pandas` và `pyarrow`.

```powershell
python scripts/convert_csv_to_parquet.py
python scripts/validate_model.py
```

CSV nguồn `Global_Superstore2.csv` nằm ở thư mục gốc và được `.gitignore`; output Parquet cùng catalog là artefact được version control. Pipeline ghi lại duy nhất `data/global_superstore`, vì vậy không xoá dữ liệu của domain khác.

## Demo phân tích bằng DuckDB

Cài DuckDB nếu cần: `pip install duckdb`. Mở DuckDB rồi chạy toàn bộ file [sql/demo_analysis.sql](sql/demo_analysis.sql). File này tạo view từ Parquet và có ba câu query mẫu: doanh thu/lợi nhuận theo tháng–category, quốc gia lỗ nhiều nhất, và SLA vận chuyển.

Ví dụ truy vấn ngắn:

```sql
SELECT order_year, SUM(sales) AS sales, SUM(profit) AS profit
FROM read_parquet(
  'data/global_superstore/facts/fact_order_line/**/*.parquet',
  hive_partitioning = true
)
WHERE order_year = 2014
GROUP BY order_year;
```

## GitHub Pages dashboard

Static site nằm trong `docs/`, gồm trang chủ project và dashboard Global Superstore. Sau khi cập nhật Parquet, xuất lại dữ liệu trình duyệt bằng:

```powershell
python scripts/build_dashboard_assets.py
```

Hướng dẫn publish GitHub Pages: [docs/README.md](docs/README.md).
