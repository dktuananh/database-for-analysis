# Từ điển dữ liệu — Student Performance

Tên cột được chuẩn hóa; `source_column` là tên gốc để đối chiếu. Khóa kỹ thuật không phải predictor. Giá trị giữ thang nguồn; không suy đoán đơn vị khi nguồn không khai báo.

## `subject_results`

Một quan sát học sinh × môn trong file gốc; không có ID học sinh đáng tin cậy.

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `record_id` | derived/aggregate | string | no | identifier | Khóa kỹ thuật ổn định trong snapshot: tên file + số dòng, không phải ID thực thể. |
| `source_file` | derived/aggregate | string | no | identifier | Tên file gốc bên trong archive nguồn. |
| `source_row` | derived/aggregate | int64 | no | identifier | Số thứ tự bản ghi trong file nguồn, bắt đầu từ 1 sau header. |
| `subject` | derived/aggregate | string | no | feature | Môn học: mathematics hoặc portuguese; derived từ file nguồn. |
| `school` | school | string | no | feature | Trường: GP hoặc MS. |
| `sex` | sex | string | no | feature | Mã giới tính F/M trong nguồn. |
| `age` | age | int64 | no | feature | Tuổi, năm. |
| `address` | address | string | no | feature | Loại nơi ở: U urban, R rural. |
| `famsize` | famsize | string | no | feature | Quy mô gia đình: LE3 <=3, GT3 >3 người. |
| `pstatus` | Pstatus | string | no | feature | Tình trạng sống chung của bố mẹ: T together, A apart. |
| `medu` | Medu | int64 | no | feature | Học vấn mẹ: 0 none, 1 primary, 2 lớp 5–9, 3 secondary, 4 higher. |
| `fedu` | Fedu | int64 | no | feature | Học vấn bố: cùng mã 0–4 như medu. |
| `mjob` | Mjob | string | no | feature | Nghề mẹ: teacher/health/services/at_home/other. |
| `fjob` | Fjob | string | no | feature | Nghề bố: teacher/health/services/at_home/other. |
| `reason` | reason | string | no | feature | Lý do chọn trường: home/reputation/course/other. |
| `guardian` | guardian | string | no | feature | Người giám hộ: mother/father/other. |
| `traveltime` | traveltime | int64 | no | feature | Thời gian đi học: 1 <15 phút, 2 15–30 phút, 3 30–60 phút, 4 >60 phút. |
| `studytime` | studytime | int64 | no | feature | Học mỗi tuần: 1 <2 giờ, 2 2–5 giờ, 3 5–10 giờ, 4 >10 giờ. |
| `failures` | failures | int64 | no | feature | Số lần trượt môn trước đó; giữ mã nguồn, xem student.txt. |
| `schoolsup` | schoolsup | string | no | feature | Hỗ trợ giáo dục thêm: yes/no. |
| `famsup` | famsup | string | no | feature | Hỗ trợ học tập từ gia đình: yes/no. |
| `paid` | paid | string | no | feature | Học thêm có trả phí cho môn học: yes/no. |
| `activities` | activities | string | no | feature | Hoạt động ngoại khóa: yes/no. |
| `nursery` | nursery | string | no | feature | Đã học mẫu giáo: yes/no. |
| `higher` | higher | string | no | feature | Muốn học bậc cao hơn: yes/no. |
| `internet` | internet | string | no | feature | Có Internet ở nhà: yes/no. |
| `romantic` | romantic | string | no | feature | Có quan hệ tình cảm: yes/no. |
| `famrel` | famrel | int64 | no | feature | Chất lượng quan hệ gia đình: ordinal 1 rất xấu đến 5 rất tốt. |
| `freetime` | freetime | int64 | no | feature | Thời gian rảnh sau học: ordinal 1 rất ít đến 5 rất nhiều. |
| `goout` | goout | int64 | no | feature | Đi chơi với bạn: ordinal 1 rất ít đến 5 rất nhiều. |
| `dalc` | Dalc | int64 | no | feature | Tiêu thụ rượu ngày làm việc: ordinal 1 rất ít đến 5 rất nhiều. |
| `walc` | Walc | int64 | no | feature | Tiêu thụ rượu cuối tuần: ordinal 1 rất ít đến 5 rất nhiều. |
| `health` | health | int64 | no | feature | Tình trạng sức khỏe tự báo cáo: ordinal 1 rất xấu đến 5 rất tốt. |
| `absences` | absences | int64 | no | feature | Số buổi vắng học theo nguồn. |
| `g1` | G1 | int64 | no | unavailable_at_default_prediction_time | Điểm kỳ 1, 0–20; chỉ dùng nếu đã biết ở thời điểm dự báo. |
| `g2` | G2 | int64 | no | unavailable_at_default_prediction_time | Điểm kỳ 2, 0–20; chỉ dùng nếu đã biết ở thời điểm dự báo. |
| `g3` | G3 | int64 | no | target | Target: điểm cuối kỳ, 0–20. |

## `subject_grade_summary`

Một dòng cho mỗi nhóm subject × school

| Cột | Cột gốc | Kiểu Parquet | Null | Vai trò | Ý nghĩa |
| --- | --- | --- | --- | --- | --- |
| `subject` | derived/aggregate | string | no | group_key | Môn học: mathematics hoặc portuguese; derived từ file nguồn. |
| `school` | derived/aggregate | string | no | group_key | Trường: GP hoặc MS. |
| `source_records` | derived/aggregate | int64 | no | aggregate | Số bản ghi ở bảng prepared chính trong nhóm, gồm dòng trùng. |
| `mean_g3` | derived/aggregate | double | no | aggregate | Trung bình g3 của các quan sát môn học trong nhóm. |
| `mean_absences` | derived/aggregate | double | no | aggregate | Trung bình absences của các quan sát môn học trong nhóm. |
