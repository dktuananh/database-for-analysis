# Energy Efficiency

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
| [building_simulations](prepared/building_simulations.parquet) | 768 | prepared | Một cấu hình công trình trong mô phỏng nguồn. |
| [orientation_load_summary](marts/orientation_load_summary.parquet) | 4 | marts | Một dòng cho mỗi nhóm orientation |

## Nguồn và tái sử dụng

Tsanas, A., & Xifara, A. (2012). Energy Efficiency [Dataset]. UCI Machine Learning Repository. [DOI](https://doi.org/10.24432/C51307). Nguồn: [UCI](https://archive.ics.uci.edu/dataset/242/energy+efficiency). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `499441eee27929a4b00417f58fd8c63c9cc14b8a71520cd0dd27fcb626738351`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "energy_efficiency/prepared/building_simulations.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

- Hình học công trình và diện tích kính liên quan thế nào đến heating/cooling load?
- Mô hình dự báo có khái quát tốt khi giữ riêng một nhóm hình dạng công trình không?

## Quy tắc phân tích và mô hình

- 768 cấu hình mô phỏng Ecotect từ 12 hình dạng công trình, không phải đo tiêu thụ điện từ 768 công trình thực tế.
- Hai target là heating_load và cooling_load. Loại cả hai khỏi X cho bài multi-output; không dùng một target để dự báo target còn lại trừ khi nó thực sự đã biết.
- orientation và glazing_area_distribution là mã category, không phải đại lượng liên tục.
- Đánh giá bằng group holdout theo hình dạng (relative_compactness/surface_area/wall_area/roof_area/overall_height), so với random split.
- File Excel có thể có dòng/cột trống cuối bảng. Chỉ đọc 10 cột X1–X8, Y1–Y2 và bỏ dòng hoàn toàn trống; phải còn đúng 768 dòng.

## Chất lượng snapshot

Validator đã vượt qua 20 kiểm tra. Bảng chính có 0 dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project energy_efficiency --offline
python scripts/validate_public_datasets.py --project energy_efficiency --verify-source
```

Query mẫu: [sql/energy_efficiency_analysis.sql](../../sql/energy_efficiency_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/energy_efficiency_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
