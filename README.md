# Model in 3D

[Gallery](https://nguyenvanduocit.github.io/esp-enclosures/) hiển thị thumbnail, kích thước và trạng thái in của từng mẫu. Chọn model để mở viewer; nút Gallery quay lại danh sách. Có tìm kiếm, link riêng dạng `#model/<id>` và tải ZIP.

| Model | Kích thước ngoài | Trạng thái |
|---|---|---|
| [ESP32-C3 + 18650](https://nguyenvanduocit.github.io/esp-enclosures/#model/esp32-c3-supermini-18650) | 60 × 85,2 × 27,2 mm, gồm nút USB | Chưa in thử |
| [ESP32-C3 SuperMini](https://nguyenvanduocit.github.io/esp-enclosures/#model/esp32-c3-supermini) | 26,4 × 32 × 20,2 mm | Chưa in thử |

## Thêm model

1. Tạo thư mục riêng chứa `viewer.html`, ảnh `thumbnail.png` tỉ lệ 4:3 và file ZIP để tải.
2. Thêm một mục vào `models.json`, theo cấu trúc của mẫu có sẵn. `id` là duy nhất, dùng chữ thường, số và dấu gạch ngang. Đường dẫn tính từ thư mục gallery. Thứ tự trong JSON là thứ tự hiển thị.
3. Chạy `python3 build_gallery.py`, rồi commit cả nguồn và `index.html` đã tạo. GitHub Pages phục vụ nhánh `main`, thư mục gốc.

`models.json` quản lý nội dung; `gallery-template.html` quản lý giao diện. Bộ dựng kiểm tra ID và sự tồn tại của thumbnail, viewer, ZIP. Không cần npm hoặc máy chủ ứng dụng. Gallery và từng viewer mở được bằng file HTML; trình duyệt cần WebGL để xem 3D.

## File thiết kế

Mỗi thư mục model có README riêng cho kích thước linh kiện, hướng in và giả định lắp ráp. STL là các chi tiết in; STEP giữ hình học CAD. Viewer V2 có cấu hình Bambu Studio, ước tính nhựa và kiểm tra lưới. Độ vừa của linh kiện và ngàm vẫn cần kiểm chứng bằng bản in.

Three.js và OrbitControls đi kèm theo giấy phép [MIT](esp32-c3-supermini-18650/vendor/LICENSE).
