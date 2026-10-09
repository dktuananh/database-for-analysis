# Catalog dữ liệu thực hành

Mỗi project có thư mục riêng trong `data/`. Tra cứu bằng máy qua [index.json](index.json).

| Project | Thư mục | Quan sát bảng chính | File Parquet | Giấy phép nguồn |
| --- | --- | ---: | ---: | --- |
| [Bank Marketing (Additional Full)](bank_marketing/README.md) | bank_marketing | 41,188 | 2 | CC-BY-4.0 |
| [Bike Sharing](bike_sharing/README.md) | bike_sharing | 17,379 | 3 | CC-BY-4.0 |
| [Energy Efficiency](energy_efficiency/README.md) | energy_efficiency | 768 | 2 | CC-BY-4.0 |
| [Global Superstore](global_superstore/metadata/project.json) | global_superstore | 51,290 | 16 | not_verified |
| [Online Retail](online_retail/README.md) | online_retail | 541,909 | 2 | CC-BY-4.0 |
| [Student Performance](student_performance/README.md) | student_performance | 1,044 | 2 | CC-BY-4.0 |
| [Wine Quality (Red + White)](wine_quality/README.md) | wine_quality | 6,497 | 2 | CC-BY-4.0 |

Số quan sát lấy từ bảng chính, không cộng dimension, aggregate hoặc bảng ngày/giờ cùng nguồn. Tổng 6 project UCI mới: 608,785 quan sát bảng chính. Global Superstore là project có sẵn và có 51,290 dòng giao dịch riêng.

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
