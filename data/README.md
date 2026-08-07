# Data project contract

Mỗi thư mục con trực tiếp của `data/` là một project phân tích độc lập. Tên thư mục dùng `snake_case` và trùng với `id` trong `metadata/project.json`.

## Bốn layer bắt buộc

| Layer | Mục đích | Quy tắc |
| --- | --- | --- |
| `dimensions/` | Entity tham chiếu đã chuẩn hóa | Một primary key không null, grain rõ ràng |
| `facts/` | Sự kiện có foreign key tới dimension | Measure phù hợp với grain; partition khi có lợi cho truy vấn |
| `marts/` | Aggregate phục vụ dashboard | Có thể tái tạo từ fact và dimension |
| `metadata/` | Project manifest và data catalog | Ghi schema, grain, key, relationship, lineage và quality checks |

## Metadata bắt buộc

- `project.json`: tên, slug, domain, độ khó, business questions và learning path.
- `data_catalog.json`: schema vật lý, business grain, primary key, foreign key, relationship và danh sách file.

Không dùng tên chung chung như `data.parquet`. Ưu tiên tên thể hiện vai trò như `fact_transaction`, `dim_customer` hoặc `monthly_revenue_kpis`.

## Definition of done cho một project

- Parquet đọc được và có compression phù hợp.
- Primary key duy nhất, foreign key không có bản ghi mồ côi ngoài quy ước đã ghi.
- Mart khớp với số liệu tổng hợp lại từ fact.
- Có ít nhất một query kiểm tra grain và một query trả lời câu hỏi kinh doanh.
- Asset dashboard được build từ Parquet, không chỉnh số liệu thủ công.
- Workspace hướng dẫn giải thích được đường đi từ dữ liệu đến kết luận.

## Minimum quality contract

| Dimension | Assertion tối thiểu |
| --- | --- |
| Completeness | Primary/foreign key và analytical measure bắt buộc không null |
| Uniqueness | Primary key duy nhất tại business grain đã công bố |
| Referential integrity | Mọi foreign key ánh xạ được tới parent dataset |
| Domain validity | Quantity dương; sales và shipping cost không âm; discount trong `[0, 1]` |
| Temporal validity | Ship date không trước order date; period filter có coverage rõ ràng |
| Reconciliation | Mart subtotal và total khớp phép tổng hợp từ fact |

Catalog hiện hành: `global_superstore/metadata/data_catalog.json`.
