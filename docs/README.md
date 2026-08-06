# GitHub Pages site

Static website cho data portfolio. Không cần backend: dashboard đọc aggregate JSON đã được xuất từ mô hình Parquet.

## Cập nhật dữ liệu website

Sau khi build lại Parquet, chạy:

```powershell
python scripts/build_dashboard_assets.py
```

Sau đó commit cả thay đổi trong `data/` và `docs/assets/data/`.

## Deploy GitHub Pages

Trong GitHub repository, mở **Settings > Pages**, chọn **Deploy from a branch**, rồi đặt:

- Branch: `main`
- Folder: `/docs`

Trang chủ sẽ là `<github-pages-url>/` và dashboard Global Superstore là `<github-pages-url>/global-superstore/`.
