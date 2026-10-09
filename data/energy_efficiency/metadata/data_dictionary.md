# Từ điển dữ liệu — Energy Efficiency

Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.

## `building_simulations`

Một cấu hình công trình trong mô phỏng nguồn.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `relative_compactness` | X1 | double | no | feature | X1: Relative compactness, giữ thang nguồn. |
| `surface_area` | X2 | double | no | feature | X2: Surface area, giữ thang nguồn. |
| `wall_area` | X3 | double | no | feature | X3: Wall area, giữ thang nguồn. |
| `roof_area` | X4 | double | no | feature | X4: Roof area, giữ thang nguồn. |
| `overall_height` | X5 | double | no | feature | X5: Overall height, giữ thang nguồn. |
| `orientation` | X6 | int64 | no | feature | X6: Mã orientation 2–5, categorical. |
| `glazing_area` | X7 | double | no | feature | X7: Glazing area, giữ thang nguồn. |
| `glazing_area_distribution` | X8 | int64 | no | feature | X8: Mã glazing area distribution 0–5, categorical. |
| `heating_load` | Y1 | double | no | target | Y1: Target heating load từ mô phỏng, giữ thang nguồn; không giả định kWh. |
| `cooling_load` | Y2 | double | no | target | Y2: Target cooling load từ mô phỏng, giữ thang nguồn; không giả định kWh. |

## `orientation_load_summary`

Một dòng cho mỗi nhóm orientation

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `orientation` | derived/aggregate | int64 | no | group_key | X6: Mã orientation 2–5, categorical. |
| `source_records` | derived/aggregate | int64 | no | aggregate | Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng. |
| `mean_heating_load` | derived/aggregate | double | no | aggregate | Trung bình heating_load theo orientation. |
| `mean_cooling_load` | derived/aggregate | double | no | aggregate | Trung bình cooling_load theo orientation. |
