# Bank Marketing (Additional Full)

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
| [campaign_contacts](prepared/campaign_contacts.parquet) | 41,188 | prepared | Một quan sát chiến dịch từ bank-additional-full.csv, không có khóa khách hàng. |
| [channel_outcomes](marts/channel_outcomes.parquet) | 6 | marts | Một dòng cho mỗi nhóm contact × poutcome |

## Nguồn và tái sử dụng

Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing [Dataset]. UCI Machine Learning Repository. [DOI](https://doi.org/10.24432/C5K306). Nguồn: [UCI](https://archive.ics.uci.edu/dataset/222/bank+marketing). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "bank_marketing/prepared/campaign_contacts.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

- Tỷ lệ đăng ký tiền gửi khác nhau thế nào theo kênh và kết quả chiến dịch trước?
- Mô hình trước cuộc gọi có cải thiện PR-AUC và recall so với baseline không?

## Quy tắc phân tích và mô hình

- Chỉ dùng bank-additional-full.csv, không ghép sample 10% hay phiên bản bank-full cũ vào cùng dữ liệu.
- Một dòng là quan sát chiến dịch theo nguồn, không phải khách hàng duy nhất; không có ID để bảo đảm tách khách hàng.
- duration chỉ biết sau cuộc gọi. Loại duration khỏi mô hình dùng trước cuộc gọi; đây là leakage quan trọng.
- unknown là category được giữ nguyên, pdays = 999 nghĩa là chưa liên hệ trước, không phải 999 ngày thông thường.
- Nguồn sắp xếp theo thời gian 05/2008–11/2010 nhưng không có ngày đầy đủ. Giữ source_row, có thể holdout theo thứ tự; không dựng ngày giả từ month.
- Fit encoder, imputer, scaler và resampling chỉ trên train. Dùng PR-AUC, precision/recall, calibration và threshold theo bài toán.

## Chất lượng snapshot

Validator đã vượt qua 17 kiểm tra. Bảng chính có 12 dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project bank_marketing --offline
python scripts/validate_public_datasets.py --project bank_marketing --verify-source
```

Query mẫu: [sql/bank_marketing_analysis.sql](../../sql/bank_marketing_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/bank_marketing_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
