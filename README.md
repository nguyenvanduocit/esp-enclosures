# Hộp in 3D cho ESP32-C3 SuperMini

Hai bản hộp cho bo đã hàn hai hàng chân hướng xuống, kèm STL, STEP, nguồn CadQuery và viewer 3D tương tác.

| Phiên bản | Kích thước ngoài | Viewer | Bộ file |
|---|---|---|---|
| V1 — ESP32-C3 | 26,4 × 32 × 20,2 mm | [Mở viewer](https://nguyenvanduocit.github.io/esp-enclosures/esp32-c3-supermini/viewer.html) | [Tải ZIP](https://nguyenvanduocit.github.io/esp-enclosures/esp32-c3-supermini/esp32-c3-supermini-enclosure.zip) |
| V2 — ESP32-C3 + 18650 | 60 × 84 × 27,2 mm | [Mở viewer](https://nguyenvanduocit.github.io/esp-enclosures/esp32-c3-supermini-18650/viewer.html) | [Tải ZIP](https://nguyenvanduocit.github.io/esp-enclosures/esp32-c3-supermini-18650/esp32-c3-supermini-18650.zip) |

[GitHub Pages](https://nguyenvanduocit.github.io/esp-enclosures/) mở viewer V2 qua `index.html`. Mỗi file `viewer.html` cũng chạy độc lập, không cần tải thư viện từ mạng. Viewer có xoay/zoom, animation mở–đóng, ẩn nắp và đo linh kiện. Chiều cao vỏ luôn đo khi lắp kín.

V2 có hai nắp độc lập, khay 18650 mua sẵn và chỗ lắp module TPS63020; không có khoang mạch sạc. Đã chừa lỗ luồn dây 8 × 6 mm qua vách ngăn, chưa có rãnh hoặc kẹp giữ dây.

Đọc README trong từng thư mục để xem kích thước linh kiện giả định, hướng in và cách tái tạo model. Các kiểm tra hình học được lưu trong `verification.json`; cả hai bản chưa được in thử. Kích thước đúng biến thể module Shopee và độ vừa của linh kiện thực vẫn cần xác minh.

Thư viện Three.js và OrbitControls đi kèm theo giấy phép [MIT](https://nguyenvanduocit.github.io/esp-enclosures/esp32-c3-supermini-18650/vendor/LICENSE).
