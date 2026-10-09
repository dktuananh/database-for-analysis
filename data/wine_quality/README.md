# Wine Quality (Red + White)

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
| [wine_samples](prepared/wine_samples.parquet) | 6,497 | prepared | Một dòng mẫu rượu trong file gốc; các vector số có thể trùng. |
| [quality_distribution](marts/quality_distribution.parquet) | 13 | marts | Một dòng cho mỗi nhóm wine_type × quality |

## Nguồn và tái sử dụng

Cortez, P., Cerdeira, A., Almeida, F., Matos, T., & Reis, J. (2009). Wine Quality [Dataset]. UCI Machine Learning Repository. [DOI](https://doi.org/10.24432/C56S3T). Nguồn: [UCI](https://archive.ics.uci.edu/dataset/186/wine+quality). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `3ed56667f4b828242bd732d7d1dd7f2861e54432239d7fa63877014cbb0304d4`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "wine_quality/prepared/wine_samples.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

- Những đặc tính hóa lý nào liên quan đến quality?
- Sai số dự báo và mất cân bằng điểm quality khác nhau thế nào giữa rượu đỏ và trắng?

## Quy tắc phân tích và mô hình

- Gộp 1.599 mẫu đỏ và 4.898 mẫu trắng, giữ wine_type và mọi dòng trùng để người học quyết định cách xử lý.
- quality là điểm ordinal 0–10. Không tự nhị phân hóa good/bad; nếu dùng classification phải công bố ngưỡng và phân phối lớp.
- Giữ các dòng có vector feature giống nhau trong cùng split để hạn chế contamination; fit scaling chỉ trên train.
- Không có brand, giá, giống nho hoặc khóa mẫu tự nhiên; record_id chỉ là khóa kỹ thuật của snapshot.

## Chất lượng snapshot

Validator đã vượt qua 29 kiểm tra. Bảng chính có 1,177 dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project wine_quality --offline
python scripts/validate_public_datasets.py --project wine_quality --verify-source
```

Query mẫu: [sql/wine_quality_analysis.sql](../../sql/wine_quality_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/wine_quality_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
