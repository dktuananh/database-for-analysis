# Bike Sharing

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
| [hourly_rentals](prepared/hourly_rentals.parquet) | 17,379 | prepared | Một giờ quan sát trong hệ thống thuê xe. |
| [daily_rentals](prepared/daily_rentals.parquet) | 731 | prepared | Một ngày aggregate chính thức từ nguồn, không phải bản ghi giờ mới. |
| [monthly_rentals](marts/monthly_rentals.parquet) | 24 | marts | Một dòng cho mỗi nhóm month |

## Nguồn và tái sử dụng

Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning Repository. [DOI](https://doi.org/10.24432/C5W894). Nguồn: [UCI](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "bike_sharing/prepared/hourly_rentals.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

- Nhu cầu xe đạp khác nhau thế nào theo giờ, ngày làm việc và mùa?
- Baseline mùa vụ và mô hình hồi quy dự báo nhu cầu tốt đến mức nào?

## Quy tắc phân tích và mô hình

- 2011–2012, Capital Bikeshare. File hour.csv thực tế có 17.379 dòng dù trang nguồn ghi 17.389; dùng số đo từ file.
- day.csv có 731 ngày là aggregate cùng hệ thống. Không nối dọc ngày và giờ rồi cộng lượt thuê.
- Không có đủ mọi giờ trong lịch. Không tự điền giờ vắng bằng zero; resample và công bố chính sách missing trước khi tạo lag.
- Dự báo rental_count: loại casual_count và registered_count vì tổng hai biến bằng target.
- Chia train/validation/test theo thời gian, rolling-origin backtest; tạo lag bằng shift trước khi rolling.
- Thời tiết đo trong giờ chỉ dùng nếu đã biết ở thời điểm dự báo; bài dự báo tương lai cần forecast thời tiết hoặc loại biến này.
- Các biến nhiệt độ, độ ẩm, gió được chuẩn hóa ở nguồn. Giữ đơn vị normalized và không tự giải chuẩn hóa aggregate ngày.
- Readme.txt gốc và trang UCI hiện tại ghi nhãn season/chuẩn hóa nhiệt độ khác nhau. Giữ mã season số, không tự gán tên mùa hoặc đổi về Celsius khi chưa thống nhất định nghĩa.

## Chất lượng snapshot

Validator đã vượt qua 64 kiểm tra. Bảng chính có 0 dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project bike_sharing --offline
python scripts/validate_public_datasets.py --project bike_sharing --verify-source
```

Query mẫu: [sql/bike_sharing_analysis.sql](../../sql/bike_sharing_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/bike_sharing_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
