# ESP32-C3 SuperMini + 18650 — V2

Thân hộp 60 × 84 × 27,2 mm cho bo đã hàn hai hàng chân hướng xuống, một viên 18650 tháo rời và module tăng/hạ áp mini. Có hai nắp độc lập; thay pin qua nắp bên trái. Không có khoang mạch sạc. Có nút bịt USB tháo rời; kích thước bao ngoài khi gắn nút là 60 × 85,2 × 27,2 mm. Bản V1 nằm ở thư mục bên cạnh và được giữ nguyên.

Mở `viewer.html` trực tiếp bằng trình duyệt có WebGL. File chạy offline, có xoay/zoom, animation mở–đóng và chế độ **Thay pin**. Sidebar có **Hiển thị** để ẩn từng chi tiết, **Đo** để bật kích thước vỏ hoặc linh kiện và **In & tải** để lấy file cùng cấu hình in. Số đo vỏ luôn tính khi lắp kín, không cộng khoảng bóc tách. Chế độ **Bịt USB** chỉ di chuyển nút bịt; chế độ thay pin giữ nó tại chỗ.

## Kéo từng chi tiết

Rê chuột lên chi tiết để làm sáng nó và hiện mũi tên. Giữ chuột trái rồi kéo theo mũi tên để tháo, kéo ngược để lắp lại. Nắp, bo, khay và pin di chuyển theo trục đứng; nút bịt USB đi ra trước; thân hộp đi xuống. ESP32 và toàn bộ chân pin di chuyển cùng nhau.

Kéo vùng trống hoặc giữ Alt khi kéo để xoay góc nhìn. Thả chuột giữ nguyên vị trí chi tiết; Esc hủy lượt kéo đang thực hiện. **Lắp lại** hoặc **Đặt lại** đưa các phần về vị trí lắp. Khi kéo, animation tạm dừng; bấm **Phát** sau đó bắt đầu lại chu kỳ từ trạng thái đóng. Nếu nhìn thẳng dọc hướng tháo, kéo lên/xuống màn hình để di chuyển chi tiết theo trục đó. Cảm ứng giữ thao tác xoay/chụm để zoom.

Đây là thao tác bóc tách minh họa, không mô phỏng va chạm trong lúc kéo. Số đo vỏ giữ kích thước lắp kín; số đo linh kiện đi theo linh kiện.

## Linh kiện và giả định

| Linh kiện | Kích thước dùng trong CAD (mm) | Nguồn / độ chắc chắn |
|---|---|---|
| PCB ESP32-C3 SuperMini | 18 × 22,5 × 1,6 | Bản tham khảo V1; vị trí linh kiện trên PCB minh họa |
| Viên 18650 | Ø18,5 × 65,3 | Giả định hình bao; chưa đo viên pin của bạn |
| Khay 1 pin, loại hở | Rộng 22 × dài 75 × cao 18 | [Linh Kiện Điện Tử 3M](https://chotroihn.vn/bo-3-hop-de-dung-pin-18650-1-pin) công bố 75 × 22 × 18 |
| Module TPS63020 | Rộng 24 × dài 34 × cao 4,5 | [Orwintech](https://www.orwintech.com/TechnologyDetail/tps63020-buck-boost-power-supply-module-step-up-down) công bố 34 × 24 × 4,5; chưa xác minh cùng biến thể Shopee |

Listing để đối chiếu: [TPS63020 của btsgo.vn trên Shopee](https://shopee.vn/product/126254005/50757366526). Đã thử Shopee MCP nhưng Chromium báo profile đang được phiên khác sử dụng; listing được tìm qua tìm kiếm web công khai. Chưa đọc được biến thể/tồn kho/giá hiện tại qua MCP. Cần đối chiếu kích thước đúng module trước khi mua hoặc in. Tên TPS63020 không xác định duy nhất kích thước PCB hay điện áp đầu ra của module.

**HIGH:** hình học và các kiểm tra trong `verification.json` đã chạy. **MEDIUM:** kích thước khay/module dựa trên thông số người bán. **LOW:** độ vừa với bộ linh kiện thực của bạn, cần đo hoặc in thử. Thiết kế chưa kiểm chứng cho viên 18650 dài hơn do đầu nút/mạch bảo vệ.

## Lắp cơ khí

- Khay pin mua sẵn đặt trong khoang trái; gờ ở đáy định vị khay. Chừa 0,8 mm bên dưới cho băng dính cố định. Dùng dải kéo luồn dưới pin để dễ nhấc ra. Mô hình khay chỉ là hình bao minh họa, không bao gồm tiếp điểm.
- ESP32 ở phía trước khoang phải, USB hướng ra cạnh ngắn. Bốn trụ đỡ mặt dưới PCB ở cao độ 12 mm; khoảng dưới PCB 10 mm chứa chân đã hàn. Các gờ chặn định vị ngang; PCB cần cố định thêm vào trụ bằng vật liệu phù hợp nếu hộp bị lật/rung. Chưa chừa kích thước đầu cắm Dupont dưới chân.
- Module nguồn nằm phía sau ESP32, trên hai thanh đỡ. Chừa 0,5 mm cho băng dính; gờ định vị chứa được footprint dài tối đa 35 mm, rộng 24 mm. Linh kiện cao tối đa 4,5 mm được dùng cho phép kiểm tra hiện tại. Hàn dây thay vì giả định có sẵn giắc/header nhô cao.
- Cửa đi dây 8 × 6 mm xuyên vách ngăn; có khoảng trống giữa hai bo. Chưa mô hình hóa dây, đầu nối và công tắc.
- Hai nắp có mép cài sâu 2,4 mm, khe hở 0,2 mm mỗi bên và bốn gân ma sát dôi cục bộ 0,08 mm. Nắp pin có rãnh bám tay, thân có hõm móng tay; nắp mạch có ba khe thoáng. Các thông số lắp cần hiệu chỉnh theo máy in.

Nút bịt USB che toàn bộ lỗ 14 × 14,2 mm ở mặt trước. Mặt ngoài 17 × 17,2 mm, dày 1,2 mm; phần gài 13,6 × 13,8 mm, sâu 1,7 mm, có bốn gân ma sát dôi 0,08 mm. Nút tì vào vỏ; trong model, đầu trong cách cổng USB trên bo 1,05 mm. Tháo nút bằng viền nhô trước khi cắm dây. Đây là nắp che cơ khí, không có gioăng kín nước. Cần in thử để chỉnh độ chặt.

## File in và tái tạo

- `base.stl`: thân, mặt đáy trên bàn in.
- `battery_lid.stl`: nắp pin, mặt ngoài trên bàn in, mép cài hướng lên.
- `electronics_lid.stl`: nắp mạch, cùng hướng in với nắp pin.
- `usb_cap.stl`: nút bịt USB, mặt ngoài phẳng đặt trên bàn in, phần gài hướng lên; không cần in lại thân hoặc hai nắp.
- `enclosure.step`: bốn chi tiết ở vị trí lắp kín; không chứa linh kiện tham khảo.
- `model.py`: nguồn CAD; `reference.json` là mesh minh họa cho viewer, không phải chi tiết cần in.
- `viewer-template.html`, `part-drag.js`, `build_viewer.py`, `vendor/`: nguồn viewer offline; Three.js 0.169.0, MIT.

```sh
uv run --python 3.12 --with cadquery==2.8.0 --with trimesh==5.1.1 python model.py
python3 build_viewer.py
```

Model kiểm tra BRep hợp lệ, STL kín/một khối, giao nhau giữa linh kiện–vỏ, nắp–nắp, cửa USB cho bao dây 12 × 6 mm, và hình quét liên tục của viên pin khi nhấc lên với nắp mạch vẫn đóng. Gân ma sát chủ đích được loại khỏi phép kiểm tra khe lắp nắp. Đường rút nút bịt theo phương thẳng ra trước cũng được kiểm tra bằng hình quét, bỏ qua gân ma sát chủ đích. STEP được đọc lại để xác nhận bốn solid hợp lệ. Những phép kiểm tra này không thay thế việc thử độ vừa, tiếp điểm pin, độ bền ngàm và cách cố định bo trên bản in thật.
