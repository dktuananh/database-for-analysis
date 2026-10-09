# Student Performance

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
| [subject_results](prepared/subject_results.parquet) | 1,044 | prepared | Một quan sát học sinh × môn trong file gốc; không có ID học sinh đáng tin cậy. |
| [subject_grade_summary](marts/subject_grade_summary.parquet) | 4 | marts | Một dòng cho mỗi nhóm subject × school |

## Nguồn và tái sử dụng

Cortez, P. (2008). Student Performance [Dataset]. UCI Machine Learning Repository. [DOI](https://doi.org/10.24432/C5TG7T). Nguồn: [UCI](https://archive.ics.uci.edu/dataset/320/student+performance). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `82ae9d66437b9808df42e8c89d2bb179c46e9cfbcf06f38abc1d20b3b747e177`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "student_performance/prepared/subject_results.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

- Phân phối điểm cuối kỳ khác nhau thế nào giữa môn Toán và tiếng Bồ Đào Nha?
- Hiệu quả dự báo G3 trước học kỳ và sau G2 khác nhau ra sao?

## Quy tắc phân tích và mô hình

- Gộp 395 dòng Toán và 649 dòng tiếng Bồ Đào Nha; 1.044 là số quan sát môn học, không phải 1.044 học sinh riêng biệt.
- Không có student ID. Các thuộc tính ghép trong tài liệu nguồn chỉ là heuristic và có thể va chạm, không tạo khóa học sinh giả.
- Nên thực hành từng môn riêng. Nếu gộp hai môn, xác định nhóm cùng học sinh theo hướng dẫn nguồn rồi audit sự mơ hồ trước group split.
- Dự báo từ đầu kỳ phải loại g1, g2 và biến chỉ biết sau thời điểm dự báo. Bài sau G2 có thể dùng g1/g2 nếu công bố thời điểm.
- Biến dạng thang thứ bậc 1–5 cần giữ nghĩa ordinal; association không chứng minh tác động nhân quả.

## Chất lượng snapshot

Validator đã vượt qua 28 kiểm tra. Bảng chính có 0 dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project student_performance --offline
python scripts/validate_public_datasets.py --project student_performance --verify-source
```

Query mẫu: [sql/student_performance_analysis.sql](../../sql/student_performance_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/student_performance_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
