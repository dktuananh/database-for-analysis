# Global Superstore Parquet Data

Bộ dữ liệu Parquet sẵn sàng cho dashboard, được chuyển đổi từ `Global_Superstore2.csv`.

## Datasets

| File | Mục đích | Số dòng |
| --- | --- | ---: |
| `data/fact_sales.parquet` | Bảng giao dịch chi tiết, có thể drill-down và lọc theo thời gian/địa lý/sản phẩm. | 51,290 |
| `data/monthly_kpis.parquet` | KPI theo tháng, tối ưu cho biểu đồ xu hướng và các thẻ tổng quan. | 48 |
| `data/country_kpis.parquet` | KPI theo quốc gia, tối ưu cho bản đồ và bảng xếp hạng. | 147 |

`data/dataset_manifest.json` cung cấp schema, kích thước và khoảng thời gian của bộ dữ liệu.

## Thay đổi so với CSV gốc

- Tên cột dùng `snake_case` để dễ dùng trong SQL và JavaScript.
- `order_date` và `ship_date` được lưu kiểu ngày; CSV gốc dùng định dạng `dd-mm-yyyy`.
- `postal_code` giữ kiểu chuỗi để không mất định dạng mã bưu chính.
- Bổ sung `order_year`, `order_month` và `ship_days` cho phân tích dashboard.
- Các file dùng Parquet + nén Zstandard, có dictionary encoding và statistics để truy vấn hiệu quả.

## Dùng trong dashboard

Sau khi repository được public, dùng URL raw dưới đây và thay `<owner>` bằng GitHub username hoặc tổ chức:

```text
https://raw.githubusercontent.com/<owner>/database-for-analysis/main/data/fact_sales.parquet
```

Ví dụ DuckDB:

```sql
SELECT order_year, SUM(sales) AS sales, SUM(profit) AS profit
FROM read_parquet('https://raw.githubusercontent.com/<owner>/database-for-analysis/main/data/fact_sales.parquet')
GROUP BY order_year
ORDER BY order_year;
```

## Tái tạo dữ liệu

Yêu cầu Python 3.10+ cùng `pandas` và `pyarrow`. Đặt CSV nguồn tại thư mục gốc, sau đó chạy:

```bash
python scripts/convert_csv_to_parquet.py
```

## Lưu ý sử dụng

CSV gốc không được đưa lên repository để tránh trùng lặp và giảm dung lượng. Hãy kiểm tra quyền sử dụng/phân phối của nguồn dữ liệu trước khi tái sử dụng hoặc xuất bản bộ dữ liệu.
