# Từ điển dữ liệu — Bike Sharing

Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.

## `hourly_rentals`

Một giờ quan sát trong hệ thống thuê xe.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `instant` | instant | int64 | no | unavailable_at_default_prediction_time | Chỉ số dòng gốc; không dùng làm predictor. |
| `date` | dteday | timestamp[ns] | no | feature | Ngày quan sát 2011–2012. |
| `season` | season | int64 | no | feature | Mã mùa 1–4 giữ nguyên. Readme gốc ghi 1 springer/2 summer/3 fall/4 winter, trang UCI ghi 1 winter/2 spring/3 summer/4 fall; nhãn chưa được thống nhất. |
| `year_code` | yr | int64 | no | feature | Mã năm: 0 = 2011, 1 = 2012. |
| `month` | mnth | int64 | no | feature | Tháng 1–12. |
| `hour` | hr | int64 | no | feature | Giờ 0–23; chỉ có ở hourly_rentals. |
| `holiday` | holiday | int64 | no | feature | Ngày nghỉ theo nguồn: 0/1. |
| `weekday` | weekday | int64 | no | feature | Ngày trong tuần, 0 Sunday đến 6 Saturday. |
| `working_day` | workingday | int64 | no | feature | 1 khi không phải cuối tuần/ngày nghỉ, còn lại 0. |
| `weather_situation` | weathersit | int64 | no | feature | Mã 1 clear, 2 mist/cloudy, 3 light snow/rain, 4 heavy rain/snow/fog; chi tiết trong Readme.txt gốc. |
| `temperature_normalized` | temp | double | no | feature | Nhiệt độ đã chuẩn hóa ở nguồn, giữ thang normalized. |
| `feels_like_normalized` | atemp | double | no | feature | Nhiệt độ cảm nhận đã chuẩn hóa ở nguồn. |
| `humidity_normalized` | hum | double | no | feature | Độ ẩm chia cho 100 ở nguồn. |
| `windspeed_normalized` | windspeed | double | no | feature | Tốc độ gió chia cho 67 ở nguồn. |
| `casual_count` | casual | int64 | no | unavailable_at_default_prediction_time | Lượt thuê khách vãng lai; thành phần của target nên không dùng khi dự báo tổng. |
| `registered_count` | registered | int64 | no | unavailable_at_default_prediction_time | Lượt thuê khách đăng ký; thành phần của target nên không dùng khi dự báo tổng. |
| `rental_count` | cnt | int64 | no | target | Tổng lượt thuê, bằng casual_count + registered_count. |
| `timestamp` | derived/aggregate | timestamp[ns] | no | feature | date + hour ở bảng giờ, timezone không được nguồn công bố. |

## `daily_rentals`

Một ngày aggregate chính thức từ nguồn, không phải bản ghi giờ mới.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `instant` | instant | int64 | no | unavailable_at_default_prediction_time | Chỉ số dòng gốc; không dùng làm predictor. |
| `date` | dteday | timestamp[ns] | no | feature | Ngày quan sát 2011–2012. |
| `season` | season | int64 | no | feature | Mã mùa 1–4 giữ nguyên. Readme gốc ghi 1 springer/2 summer/3 fall/4 winter, trang UCI ghi 1 winter/2 spring/3 summer/4 fall; nhãn chưa được thống nhất. |
| `year_code` | yr | int64 | no | feature | Mã năm: 0 = 2011, 1 = 2012. |
| `month` | mnth | int64 | no | feature | Tháng 1–12. |
| `holiday` | holiday | int64 | no | feature | Ngày nghỉ theo nguồn: 0/1. |
| `weekday` | weekday | int64 | no | feature | Ngày trong tuần, 0 Sunday đến 6 Saturday. |
| `working_day` | workingday | int64 | no | feature | 1 khi không phải cuối tuần/ngày nghỉ, còn lại 0. |
| `weather_situation` | weathersit | int64 | no | feature | Mã 1 clear, 2 mist/cloudy, 3 light snow/rain, 4 heavy rain/snow/fog; chi tiết trong Readme.txt gốc. |
| `temperature_normalized` | temp | double | no | feature | Nhiệt độ đã chuẩn hóa ở nguồn, giữ thang normalized. |
| `feels_like_normalized` | atemp | double | no | feature | Nhiệt độ cảm nhận đã chuẩn hóa ở nguồn. |
| `humidity_normalized` | hum | double | no | feature | Độ ẩm chia cho 100 ở nguồn. |
| `windspeed_normalized` | windspeed | double | no | feature | Tốc độ gió chia cho 67 ở nguồn. |
| `casual_count` | casual | int64 | no | unavailable_at_default_prediction_time | Lượt thuê khách vãng lai; thành phần của target nên không dùng khi dự báo tổng. |
| `registered_count` | registered | int64 | no | unavailable_at_default_prediction_time | Lượt thuê khách đăng ký; thành phần của target nên không dùng khi dự báo tổng. |
| `rental_count` | cnt | int64 | no | target | Tổng lượt thuê, bằng casual_count + registered_count. |

## `monthly_rentals`

Một dòng cho mỗi nhóm month

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `month` | derived/aggregate | timestamp[ns] | no | group_key | Tháng quan sát, lưu ngày đầu tháng. |
| `source_records` | derived/aggregate | int64 | no | aggregate | Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng. |
| `rental_count` | derived/aggregate | int64 | no | aggregate | Tổng lượt thuê của các giờ quan sát trong tháng. |
| `casual_count` | derived/aggregate | int64 | no | aggregate | Tổng lượt thuê khách vãng lai của các giờ quan sát trong tháng. |
| `registered_count` | derived/aggregate | int64 | no | aggregate | Tổng lượt thuê khách đăng ký của các giờ quan sát trong tháng. |
