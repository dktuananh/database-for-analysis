# Từ điển dữ liệu — Wine Quality (Red + White)

Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.

## `wine_samples`

Một dòng mẫu rượu trong file gốc; các vector số có thể trùng.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `wine_type` | derived/aggregate | string | no | feature | red/white, derived từ file nguồn. |
| `fixed_acidity` | fixed acidity | double | no | feature | Fixed acidity, giữ thang số gốc; archive không khai báo đơn vị. |
| `volatile_acidity` | volatile acidity | double | no | feature | Volatile acidity, giữ thang số gốc. |
| `citric_acid` | citric acid | double | no | feature | Citric acid, giữ thang số gốc. |
| `residual_sugar` | residual sugar | double | no | feature | Residual sugar, giữ thang số gốc. |
| `chlorides` | chlorides | double | no | feature | Chlorides, giữ thang số gốc. |
| `free_sulfur_dioxide` | free sulfur dioxide | double | no | feature | Free sulfur dioxide, giữ thang số gốc. |
| `total_sulfur_dioxide` | total sulfur dioxide | double | no | feature | Total sulfur dioxide, giữ thang số gốc. |
| `density` | density | double | no | feature | Density, giữ thang số gốc. |
| `ph` | pH | double | no | feature | pH của mẫu; không có đơn vị. |
| `sulphates` | sulphates | double | no | feature | Sulphates, giữ thang số gốc. |
| `alcohol` | alcohol | double | no | feature | Alcohol, giữ thang số gốc. |
| `quality` | quality | int64 | no | target | Target: điểm chất lượng sensory, ordinal 0–10. |

## `quality_distribution`

Một dòng cho mỗi nhóm wine_type × quality

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `wine_type` | derived/aggregate | string | no | group_key | red/white, derived từ file nguồn. |
| `quality` | derived/aggregate | int64 | no | group_key | Target: điểm chất lượng sensory, ordinal 0–10. |
| `source_records` | derived/aggregate | int64 | no | aggregate | Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng. |
| `mean_alcohol` | derived/aggregate | double | no | aggregate | Trung bình alcohol theo wine_type × quality. |
