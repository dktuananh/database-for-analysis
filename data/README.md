# Quy ước kho dữ liệu

Mỗi thư mục con của `data/` là một project dữ liệu độc lập, dùng tên `snake_case` trùng với `metadata/project.json.id`. Project học tập ở nơi khác có thể đọc file trực tiếp.

Danh sách: [CATALOG.md](CATALOG.md). Registry cho chương trình: [index.json](index.json).

## Hai mô hình lưu trữ

Bộ observation dùng cho machine learning chọn `tabular_snapshot`, gồm raw/prepared/marts/metadata. Global Superstore dùng mô hình `dimensional`, gồm dimensions/facts/marts/metadata. Chọn theo grain và bài tập, không tạo dimension hoặc key thực thể giả.

| Layer | Nội dung | Quy tắc |
| --- | --- | --- |
| `raw/` | Snapshot tải từ nguồn | Không sửa byte nguồn; lưu URL, thời điểm lấy, SHA-256 và giấy phép |
| `prepared/` | Observation chuẩn hóa tên cột/kiểu | Giữ giá trị gốc và provenance; công bố biến derived và dòng bị loại |
| `dimensions/` | Entity tham chiếu trong dimensional model | Primary key không null và duy nhất, grain rõ |
| `facts/` | Sự kiện trong dimensional model | Foreign key hợp lệ, measure đúng grain, partition khi có lợi |
| `marts/` | Bảng tổng hợp | Tái tạo được từ bảng chính, công thức và population rõ |
| `metadata/` | Hợp đồng và kiểm tra | Manifest, schema, dictionary, source lineage, license, chất lượng |

## Metadata và tài liệu

- `project.json`: id, tên, domain, status, bảng chính, nguồn, câu hỏi thực hành và giới hạn.
- `data_catalog.json`: đường dẫn, số dòng, grain, schema vật lý, nullability, key, lineage và SHA-256.
- `data_dictionary.md`: ý nghĩa, tên cột gốc, thang đo/đơn vị đã xác minh, target và thời điểm có sẵn.
- `quality_report.json`: assertion đã chạy, null, trùng, miền giá trị và vấn đề được giữ lại có chủ đích.
- `LICENSE.md`: ghi nguồn tác giả, DOI/URL, liên kết giấy phép và mô tả thay đổi.
- README từng project: cách đọc, quy tắc xử lý, câu hỏi gợi ý, split phù hợp và lệnh tái tạo.

Trong 6 project UCI mới, `path` của logical dataset tính từ thư mục project. Catalog Global Superstore cũ dùng đường dẫn tính từ layer; `index.json` chuẩn hóa cả hai thành đường dẫn tính từ repository root. Wildcard của Superstore giữ nguyên để engine đọc Hive partition.

`record_id` của snapshot chỉ là tên file + số thứ tự bản ghi. Nó giúp đối chiếu raw, không chứng minh hai dòng thuộc hai khách hàng, học sinh hoặc mẫu khác nhau.

## Chất lượng phụ thuộc domain

Không áp quy tắc quantity dương của Global Superstore lên Online Retail: lượng âm có thể là điều chỉnh/hoàn hàng. Missing có ý nghĩa và `unknown`/sentinel được giữ để người học chọn chính sách. Duplicate observation được báo cáo; duplicate primary key luôn làm validator thất bại.

Không impute, scale, encode, resample hoặc fit feature selection trên toàn bộ dataset. Thực hiện trong project học tập sau khi chia tập phù hợp. Công bố thời điểm dự báo để loại leakage và giữ test cuối cho đánh giá.

`passed` nghĩa là snapshot phù hợp hợp đồng đã công bố. Người học vẫn cần EDA và xử lý theo mục đích. Dữ liệu prepared và raw cho phép thực hành ở hai mức khác nhau.

## Definition of done

1. Có file dữ liệu thực tế, đọc được, dùng Zstandard cho Parquet.
2. Nguồn và quyền phân phối được kiểm tra, raw có checksum đã pin.
3. Key/schema/count/domain qua validator, null/trùng/sentinel có chính sách rõ.
4. Mart reconcile với observation; không cộng observation và aggregate.
5. Có query kiểm tra grain và query trả lời câu hỏi domain.
6. Tái tạo offline từ raw và kiểm tra giá trị với nguồn được.

Website/notebook kết quả là phần mở rộng tùy chọn. `data_ready` đủ để project khác dùng dữ liệu; Global Superstore có workspace/dashboard trong `docs/` với trạng thái `published` từ trước.

## Quy tắc Global Superstore

Các kiểm tra cũ vẫn áp dụng riêng cho model đó: primary key duy nhất, foreign key không mồ côi, quantity dương, sales/shipping cost không âm, discount trong [0, 1], ship date không trước order date và marts reconcile. Catalog: [global_superstore/metadata/data_catalog.json](global_superstore/metadata/data_catalog.json).
