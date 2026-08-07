# GitHub Pages site

Website tĩnh cho Data Workbench. Không cần backend: analysis workspace đọc aggregate JSON được xuất từ mô hình Parquet.

## Chạy local

```powershell
python scripts/build_dashboard_assets.py
python -m http.server 8000 --directory docs
```

Mở:

- Thư viện project: `http://localhost:8000/`
- Global Superstore: `http://localhost:8000/global-superstore/`

Không mở trực tiếp file HTML bằng `file://` vì trình duyệt có thể chặn request tới JSON asset.

## Cập nhật dữ liệu website

Sau khi build lại Parquet, chạy:

```powershell
python scripts/validate_model.py
python scripts/build_dashboard_assets.py
```

Commit thay đổi trong `data/` và `docs/assets/data/`. File JSON chỉ chứa aggregate cần cho UI; Parquet vẫn là source of truth.

## Deploy GitHub Pages

Trong GitHub repository, mở **Settings > Pages**, chọn **Deploy from a branch**, sau đó đặt:

- Branch: `main`
- Folder: `/docs`

Route project giữ dạng `<github-pages-url>/<project-slug>/`.
