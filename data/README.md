# Data layout contract

Mỗi thư mục con trực tiếp của `data/` là một data domain độc lập. Một domain phải có bốn layer sau:

| Layer | Mục đích |
| --- | --- |
| `dimensions/` | Entity tham chiếu đã chuẩn hoá, có primary key và grain rõ ràng. |
| `facts/` | Sự kiện có foreign key tới dimension; partition theo cột truy vấn phổ biến khi dữ liệu đủ lớn. |
| `marts/` | Aggregate hoặc bảng phục vụ dashboard, tái tạo được từ facts/dimensions. |
| `metadata/` | Catalog JSON: schema vật lý, business grain, primary/foreign key, lineage và kiểm tra chất lượng. |

Không dùng tên file chung chung như `data.parquet` hoặc đặt Parquet của domain khác trực tiếp ở `data/`. Domain mới cần có pipeline build và validator riêng, sau đó thêm mô tả vào README cấp repository.

Catalog hiện hành: `global_superstore/metadata/data_catalog.json`.
