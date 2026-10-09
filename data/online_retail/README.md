# Online Retail

Dữ liệu cho thực hành độc lập từ Python, R, DuckDB, Polars hoặc Spark. Các bảng prepared chưa được impute, encode, scale hoặc chia train/test.

| File | Số dòng | Layer | Grain |
| --- | ---: | --- | --- |
| [invoice_lines](prepared/invoice_lines.parquet) | 541,909 | prepared | Một dòng dữ liệu giao dịch nguồn, bao gồm điều chỉnh, hoàn/hủy và trùng. |
| [monthly_transactions](marts/monthly_transactions.parquet) | 13 | marts | Một dòng cho mỗi nhóm month |

## Nguồn và tái sử dụng

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. [DOI](https://doi.org/10.24432/C5BW33). Nguồn: [UCI](https://archive.ics.uci.edu/dataset/352/online+retail). Giấy phép: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), xem [LICENSE.md](LICENSE.md).

Archive gốc được giữ nguyên ở [raw/source.zip](raw/source.zip). Tên member đã dùng nằm trong `lineage` của [catalog](metadata/data_catalog.json); bank/student có ZIP lồng nhau. SHA-256 của archive: `f5385cbb54bbebf7196389109c6b0621faab0c304e3702548165e71c84aede8b`.

## Đọc từ project khác

```python
from pathlib import Path
import pandas as pd

# Thay bằng đường dẫn tuyệt đối tới checkout của kho dữ liệu trên máy bạn.
data_root = Path(r"D:/DKTA/project/database-for-analysis/data")
df = pd.read_parquet(data_root / "online_retail/prepared/invoice_lines.parquet")
print(df.shape)
```

Không đưa `record_id`, `source_file`, `source_row` vào predictor. Đọc [từ điển dữ liệu](metadata/data_dictionary.md) để hiểu đơn vị, vai trò và tên cột gốc.

## Bài tập gợi ý

- Giá trị giao dịch có dấu thay đổi thế nào theo tháng và quốc gia?
- RFM của khách hàng thay đổi thế nào khi xử lý hoàn/hủy và dòng trùng?
- Sản phẩm nào thường xuất hiện cùng trong một hóa đơn bán hàng?

## Quy tắc phân tích và mô hình

- Giữ toàn bộ 541.909 dòng, cả null, số lượng/giá âm và dòng trùng. Đây là dữ liệu để học xử lý chất lượng.
- InvoiceNo không phải khóa dòng. StockCode có mã dịch vụ/điều chỉnh; Description có thể thay đổi cho cùng mã.
- line_amount_gbp = quantity × unit_price_gbp; đây là giá trị có dấu theo nguồn, chưa phải doanh thu kế toán đã đối soát.
- Mart tháng dùng tất cả dòng, không loại trùng. Tháng 12/2011 chỉ có đến ngày 09 nên không so tăng trưởng nguyên tháng.
- RFM cần khách hàng có ID, quy tắc hoàn/hủy và trùng được công bố. Chốt ngày quan sát rồi chỉ dùng lịch sử trước ngày đó.
- Market basket thường giới hạn hóa đơn không hủy, quantity > 0, unit_price_gbp > 0; công bố cách xử lý mã phi sản phẩm.
- Cohort chỉ đo khách hàng quan sát được trong snapshot, không có lịch sử trước 12/2010 hoặc sau 09/12/2011.

## Chất lượng snapshot

Validator đã vượt qua 14 kiểm tra. Bảng chính có 5,268 dòng giá trị trùng sau dòng đầu (bỏ khóa kỹ thuật khi so sánh). Null khác zero: `{"description": 1454, "customer_id": 135080}`.

Xem [quality_report.json](metadata/quality_report.json) để biết null từng cột, miền số, target và các vấn đề được giữ lại. Trạng thái passed nghĩa là dữ liệu phù hợp hợp đồng đã công bố, không có nghĩa dữ liệu thô đã sạch.

## Tái tạo và kiểm tra

Chạy từ repository root:

```powershell
python scripts/ingest_public_datasets.py --project online_retail --offline
python scripts/validate_public_datasets.py --project online_retail --verify-source
```

Query mẫu: [sql/online_retail_analysis.sql](../../sql/online_retail_analysis.sql). Trong Python với `duckdb`:

```python
import duckdb
sql = Path("sql/online_retail_analysis.sql").read_text(encoding="utf-8")
result = duckdb.connect().execute(sql).df()
```

Parquet là dữ liệu có kiểu để thực hành; marts chỉ dành cho aggregate. Raw dùng để tự làm lại pipeline hoặc đối chiếu. Không cộng số dòng marts vào số quan sát nguồn.
