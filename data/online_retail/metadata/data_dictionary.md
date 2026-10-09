# Từ điển dữ liệu — Online Retail

Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.

## `invoice_lines`

Một dòng dữ liệu giao dịch nguồn, bao gồm điều chỉnh, hoàn/hủy và trùng.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `invoice_no` | InvoiceNo | string | no | feature | Mã hóa đơn; bắt đầu bằng C/c chỉ hủy theo nguồn. Không duy nhất tại grain dòng. |
| `stock_code` | StockCode | string | no | feature | Mã sản phẩm hoặc mã dịch vụ/điều chỉnh, giữ dạng text. |
| `description` | Description | string | yes | feature | Mô tả sản phẩm gốc; cho phép null, không tự điền hoặc chuẩn hóa nội dung. |
| `quantity` | Quantity | int64 | no | feature | Số lượng có dấu từ nguồn; gồm giá trị âm. |
| `invoice_date` | InvoiceDate | timestamp[ns] | no | feature | Thời điểm hóa đơn, timezone không được nguồn công bố. |
| `unit_price_gbp` | UnitPrice | double | no | feature | Giá một đơn vị theo bảng nguồn, GBP; giữ cả zero và âm. |
| `customer_id` | CustomerID | string | yes | feature | Mã khách hàng dạng text; null nghĩa là nguồn không có ID, không phải một khách hàng chung. |
| `country` | Country | string | no | feature | Quốc gia theo dữ liệu nguồn. |
| `is_cancellation` | derived/aggregate | bool | no | feature | Cờ derived khi invoice_no bắt đầu bằng C/c. |
| `line_amount_gbp` | derived/aggregate | double | no | feature | quantity × unit_price_gbp, giá trị có dấu của dòng theo nguồn, GBP. |

## `monthly_transactions`

Một dòng cho mỗi nhóm month

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `month` | derived/aggregate | timestamp[ns] | no | group_key | Tháng quan sát, lưu ngày đầu tháng. |
| `source_records` | derived/aggregate | int64 | no | aggregate | Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng. |
| `invoices` | derived/aggregate | int64 | no | aggregate | Số invoice_no distinct trong tháng, gồm hóa đơn hủy. |
| `identified_customers` | derived/aggregate | int64 | no | aggregate | Số customer_id distinct không null trong tháng; không cộng qua các tháng. |
| `cancellation_lines` | derived/aggregate | int64 | no | aggregate | Số dòng có cờ hủy theo prefix hóa đơn. |
| `signed_quantity` | derived/aggregate | int64 | no | aggregate | Tổng quantity có dấu của tất cả dòng trong nhóm. |
| `signed_amount_gbp` | derived/aggregate | double | no | aggregate | Tổng quantity × unit_price_gbp của tất cả dòng, GBP. |
