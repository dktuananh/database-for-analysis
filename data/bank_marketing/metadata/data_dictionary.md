# Từ điển dữ liệu — Bank Marketing (Additional Full)

Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.

## `campaign_contacts`

Một quan sát chiến dịch từ bank-additional-full.csv, không có khóa khách hàng.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `age` | age | int64 | no | feature | Tuổi theo nguồn, năm. |
| `job` | job | string | no | feature | Nghề nghiệp dạng category, có unknown. |
| `marital` | marital | string | no | feature | Tình trạng hôn nhân; divorced gồm ly hôn/góa theo nguồn. |
| `education` | education | string | no | feature | Trình độ học vấn dạng category. |
| `default` | default | string | no | feature | Có tín dụng vỡ nợ: yes/no/unknown. |
| `housing` | housing | string | no | feature | Có khoản vay nhà: yes/no/unknown. |
| `loan` | loan | string | no | feature | Có khoản vay cá nhân: yes/no/unknown. |
| `contact` | contact | string | no | feature | Kênh liên hệ cellular/telephone. |
| `month` | month | string | no | feature | Tháng của lần liên hệ cuối; không có năm đầy đủ. |
| `day_of_week` | day_of_week | string | no | feature | Ngày trong tuần của lần liên hệ cuối. |
| `duration` | duration | int64 | no | unavailable_at_default_prediction_time | Thời lượng cuộc gọi cuối, giây. Chỉ biết sau cuộc gọi, loại khỏi dự báo trước cuộc gọi. |
| `campaign` | campaign | int64 | no | feature | Số lần liên hệ trong chiến dịch hiện tại, gồm lần cuối. |
| `pdays` | pdays | int64 | no | feature | Số ngày kể từ chiến dịch trước; 999 là chưa từng liên hệ, giữ sentinel. |
| `previous` | previous | int64 | no | feature | Số lần liên hệ trước chiến dịch hiện tại. |
| `poutcome` | poutcome | string | no | feature | Kết quả chiến dịch trước: failure/nonexistent/success. |
| `emp_var_rate` | emp.var.rate | double | no | feature | Employment variation rate, chỉ số theo quý từ nguồn. |
| `cons_price_idx` | cons.price.idx | double | no | feature | Consumer price index, chỉ số theo tháng từ nguồn. |
| `cons_conf_idx` | cons.conf.idx | double | no | feature | Consumer confidence index, chỉ số theo tháng từ nguồn. |
| `euribor3m` | euribor3m | double | no | feature | Euribor kỳ hạn 3 tháng, chỉ số theo ngày từ nguồn. |
| `nr_employed` | nr.employed | double | no | feature | Number of employees, chỉ số theo quý từ nguồn; giữ đơn vị/thang gốc. |
| `subscribed` | y | string | no | target | Target: đăng ký tiền gửi, yes/no; đổi tên từ y, không đổi nhãn. |

## `channel_outcomes`

Một dòng cho mỗi nhóm contact × poutcome

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `contact` | derived/aggregate | string | no | group_key | Kênh liên hệ cellular/telephone. |
| `poutcome` | derived/aggregate | string | no | group_key | Kết quả chiến dịch trước: failure/nonexistent/success. |
| `source_records` | derived/aggregate | int64 | no | aggregate | Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng. |
| `subscribers` | derived/aggregate | int64 | no | aggregate | Số quan sát subscribed = yes trong nhóm. |
| `subscription_rate` | derived/aggregate | double | no | aggregate | subscribers / source_records tại đúng nhóm, không lấy trung bình các tỷ lệ. |
