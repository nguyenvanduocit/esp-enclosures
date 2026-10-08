# Bàn in

[App](https://nguyenvanduocit.github.io/esp-enclosures/) dùng một viewer cho tất cả model. Gallery, màn hình model 3D (`#model/<id>`) và màn hình mô phỏng in (`#print/<id>`) chuyển trong cùng trang.

Mỗi model là một file `model.py`. `printkit` dựng CAD, kiểm tra, xuất STL/STEP và sinh `model.json` cho viewer từ cùng các hằng số đó.

```text
printkit/                  Toolkit Python: khai báo, CAD, kiểm tra, xuất, đóng gói
printkit/library/          Linh kiện tham khảo dùng lại (điện tử…)
models/<id>/model.py       Nguồn duy nhất của model
models/<id>/README.md      Ghi chú, giả định, nguồn số liệu
models/<id>/thumbnail.png  Ảnh gallery (chụp tay)
index.html, viewer/        App xem model; viewer/vendor/ là Three.js 0.169.0, MIT
model.schema.json          Hợp đồng giữa printkit và viewer, schemaVersion: 1
models.json                Danh sách model.json
```

Các file khác trong `models/<id>/` là file sinh ra (`*.stl`, `reference/`, `assembly.step`, `model.json`, `verification.json`, `<id>.zip`). Không sửa tay; chạy lại lệnh.

## Lệnh

```sh
uv run printkit new <id>     # tạo models/<id>/ từ mẫu chạy được, dựng luôn, rồi thêm vào models.json
uv run printkit cad <id>     # dựng CAD, chạy kiểm tra, ghi STL/STEP/model.json/verification.json
uv run printkit slice <id>   # như cad, rồi slice tất cả chi tiết in trên một bàn P1S bằng Bambu Studio
uv run printkit build        # kiểm tra mọi model, gắn phiên bản JS/CSS, đóng gói ZIP offline
uv run pytest && node --test tests/*.test.js
python3 -m http.server 8000  # mở http://localhost:8000
```

`cad` chỉ ghi file khi mọi bước đều qua: BRep hợp lệ và một khối, STL kín, mọi `@model.check` không va chạm, `max_overhang_mm2` (nếu khai báo) không bị vượt, STEP đọc lại đúng số khối. Lỗi thì giữ nguyên file cũ. Khi ghi, `cad` chỉ xóa file mà lần chạy trước đã sinh ra (theo `model.json` cũ); file khác trong thư mục model được giữ nguyên.

`slice` ghi thêm `print/<id>.gcode.3mf` (mở trong Bambu Studio, gửi thẳng sang P1S) và `print/layers.json` (đường chạy đầu in từng lớp cho viewer), cùng khối `print` và mục **Kết quả slice** trong `model.json` với khối lượng nhựa và thời gian thật. `cad` chạy riêng sẽ xóa `print/` của lần slice trước vì nó không còn khớp hình học. Cần cài Bambu Studio: `brew install --cask bambu-studio`.

Với model đã `slice`, màn hình model có nút **Mô phỏng in** mở `#print/<id>`: màn hình riêng chỉ có bàn in và đường chạy đầu in. Kéo thanh lớp hoặc bấm phát để chạy từng lớp, bật/tắt từng loại đường (thành ngoài, thành trong, infill…); các lớp bên dưới lớp đang xem được làm mờ. Sidebar có khối lượng nhựa, thời gian và số lớp từ khối `print`, và nút **Xem mô hình 3D** để quay lại. Dữ liệu đọc từ `print/layers.json` do `slice` sinh ra; model chưa slice không hiện nút này và không tải dữ liệu in, còn `#print/<id>` của nó báo chưa có dữ liệu in.

`cad` in cảnh báo hướng in ra stderr, dạng `warning: lid: set print_rotation to (0, 0, 180) …`: giá trị gợi ý là `print_rotation` tuyệt đối, dán thẳng vào `model.py`. Cùng thông tin nằm trong `verification.json`: khối `printability` (mỗi chi tiết có `overhang_mm2`, `bridges`, xếp hạng 6 hướng in `orientations`) và danh sách `warnings`.

## Khai báo model

Tọa độ mm, trục Z hướng lên. `printkit new <id>` sinh `models/<id>/model.py` chạy được ngay; sửa file đó thay vì viết từ đầu.

Dựng mỗi chi tiết **ở vị trí lắp**. `print_rotation` (Euler XYZ, độ) xoay chi tiết lên bàn in; printkit đặt nó xuống Z = 0, căn giữa XY, xuất STL theo hướng in và tính `position`/`rotation` cho viewer.

```python
from printkit import Box, Drag, Model, Solid, dim
from printkit.checks import clear

model = Model('wall-hook', title='Móc treo', description='…', category='Gia dụng', status='Bản nháp',
              thumbnail='thumbnail.png', dimensions=(W, L, H), camera={…}, grid={…}, print_info={…})

@model.part('body', 'Thân', color='#367c85', drag=Drag((0, 0, 1), 30), print_rotation=(0, 180, 0),
            max_overhang_mm2=50)
def body():
    return …  # CadQuery, vị trí lắp

model.reference('screw', 'Vít', [Box('head', (8, 8, 3), (0, 0, 1.5), '#c3cbd0')])
model.measure('size', 'Kích thước', kind='case', follow='body',
              lines=[dim((-W/2, -L/2, 0), (W/2, -L/2, 0), offset=(0, -6, 0), name='Rộng')])
model.animation('lift', 'Nhấc lên', duration=6, open_pose={…}, tracks={…}, camera=[…], measure_reveal=(0.34, 0.64))

@model.check('Screw clears body')
def screw_clear():
    clear(screw_envelope, body=body())
```

| API | Ý nghĩa |
|---|---|
| `model.part` | Chi tiết in; hàm dựng chạy một lần và có thể gọi lại trong kiểm tra. `max_overhang_mm2` đặt trần diện tích overhang (mm²); vượt trần thì `cad` lỗi |
| `model.reference` | Linh kiện tham khảo: `Box` thành khối hộp của viewer, `Solid` thành `reference/<name>.stl` |
| `dim(a, b, offset, name)` | Đường đo cách hai điểm neo một đoạn `offset`; nhãn tính từ độ dài thật |
| `model.animation` | Keyframe là độ dịch so với vị trí lắp, `time` từ 0 đến 1, bắt đầu và kết thúc ở vị trí lắp; `pulse(value)` sinh keyframe nghỉ, di chuyển tới `value`, giữ, rồi về |
| `model.check` | Ném `CheckFailed` khi sai; trả về dict để ghi số đo vào `verification.json` |

`Drag(axis, max_distance)`: `axis` là vector đơn vị trong hệ tọa độ thế giới; `max_distance` là khoảng kéo tối đa. Đường đo khai báo ở tư thế lắp kín; `follow` chỉ dịch chuyển đường đo cùng chi tiết; `variants` chọn bộ đường đo khác khi một chi tiết bị ẩn. Chưa mô phỏng va chạm khi kéo và chưa kiểm chứng độ vừa bằng bản in thật.

`Print(layer, first_layer, walls, infill=(mật độ %, kiểu), supports, brim='auto'|0|mm, filament='PLA', extra={khóa Bambu Studio: giá trị})` khai báo cấu hình slice chung cho cả bàn in, truyền vào `Model(..., print=Print(...))`; `extra` nhận khóa process thô của Bambu Studio. `slice` báo lỗi nếu Bambu Studio không áp dụng đúng một thiết lập. Số liệu từng chi tiết trong **Kết quả slice** tính cho việc in riêng chi tiết đó nên không cộng lại thành số của cả bàn in.

ZIP offline chứa cả `model.py` để đọc; chạy lại nó cần bộ công cụ `printkit` trong repo này (không nằm trong ZIP).
