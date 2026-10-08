# Bàn in

[App](https://nguyenvanduocit.github.io/esp-enclosures/) dùng một viewer cho tất cả model. Gallery và model chuyển trong cùng trang, theo URL `#model/<id>`.

```text
index.html                 Giao diện chung
viewer/                    Render, kéo chi tiết, đo, animation, CSS
viewer/vendor/             Three.js / OrbitControls 0.169.0, MIT
model.schema.json          JSON Schema 2020-12, schemaVersion: 1
models.json                Danh sách đường dẫn model.json
<model-id>/
  model.json               Dữ liệu model
  *.stl, enclosure.step    File in / CAD
  reference/               Mesh linh kiện tham khảo (nếu có)
  model.py                 Nguồn CAD
  thumbnail.png
  viewer.html              Chuyển hướng link cũ về app
```

## Chạy và kiểm tra

```sh
python3 -m http.server 8000
# Mở http://localhost:8000

uv run build.py
node --test tests/*.test.js
uv run --with jsonschema==4.23.0 python -m unittest discover -s tests
```

`build.py` kiểm tra schema, đường dẫn asset, ID và tham chiếu, hướng kéo, giới hạn di chuyển, thứ tự keyframe. Sau đó tạo ZIP cho từng model. Trong ZIP, mở `index.html` trực tiếp để dùng offline; HTML này được sinh từ cùng nguồn app, chứa thư viện và dữ liệu của model đó. Không sửa file sinh ra.

GitHub Pages phục vụ thư mục gốc. App online tải mesh khi mở model; thư viện và UI chỉ có một bản dùng chung. Các link `*/viewer.html` cũ vẫn hoạt động bằng chuyển hướng.

## Khai báo model

Schema đầy đủ nằm trong [model.schema.json](model.schema.json); hai `model.json` có sẵn là ví dụ chạy được.

| Trường | Ý nghĩa |
|---|---|
| `parts` | ID, tên, loại `print`/`reference`, mesh, vị trí và góc lắp, hướng kéo |
| `measurements` | Đường đo, nhãn, chi tiết đi theo; biến thể khi một chi tiết bị ẩn |
| `animations` | Thời lượng, keyframe theo chi tiết, chuyển động camera, thời gian hiện số đo |
| `camera`, `grid` | Góc nhìn mặc định, giới hạn zoom, góc nhìn có sẵn và lưới |
| `printInfo`, `downloads` | Thông tin in và file tải |
| `title`, `thumbnail`, `dimensions`, `status` | Nội dung gallery |

Tọa độ dùng mm, trục Z hướng lên. `position` là vị trí lắp; `rotation` là góc Euler XYZ theo **độ**. Mesh STL giữ tọa độ trong file; mesh `box` khai báo `size` và `position` trong chi tiết. Đường dẫn asset tính từ thư mục chứa `model.json`.

`drag.axis` là vector đơn vị trong hệ tọa độ thế giới; `maxDistance` là khoảng kéo tối đa. Animation v1 hỗ trợ **tịnh tiến**: giá trị keyframe là độ dịch chuyển so với vị trí lắp, không cộng dồn qua các frame. `time` chạy từ 0 đến 1, nội suy smoothstep. Mỗi chu kỳ bắt đầu và kết thúc ở vị trí lắp, chạy một lượt. `openPose` là trạng thái của nút **Tách rời**.

Ví dụ một track kéo chi tiết `drawer` ra 30 mm theo X rồi đóng:

```json
{"part":"drawer","keyframes":[
  {"time":0,"value":[0,0,0]},
  {"time":0.4,"value":[30,0,0]},
  {"time":0.7,"value":[30,0,0]},
  {"time":1,"value":[0,0,0]}
]}
```

Đường đo khai báo trong tọa độ lắp kín. `followPart` chỉ dịch chuyển đường đo cùng chi tiết; khoảng bóc tách không làm tăng kích thước. `variants[].whenHidden` chọn bộ đường đo khác, chẳng hạn chiều dài vỏ khi tháo nút USB. Nhãn là dữ liệu thiết kế cần cập nhật cùng CAD.

Để thêm model: tạo thư mục cùng tên `id`, thêm `model.json` và asset, ghi đường dẫn vào `models.json`, rồi chạy build. Không cần sửa HTML hoặc JavaScript. Chưa mô phỏng va chạm và chưa kiểm chứng độ vừa bằng bản in thật.
